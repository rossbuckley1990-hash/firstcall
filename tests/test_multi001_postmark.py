"""Mock-only cohort checks; subprocess and network are blocked in every test."""
from hashlib import sha256
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from firstcall.agents.codex_live import AgentResult
import firstcall.agents.codex_live as live
import firstcall.multi001_postmark as r
from firstcall.postmark_preflight import PostmarkPreflight

TOKEN = 'synthetic-postmark-credential'
NONCE = 'abcdef123456'


@pytest.fixture(autouse=True)
def no_live_work(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError('real processes/network forbidden')
    monkeypatch.setattr('subprocess.run', blocked)
    monkeypatch.setattr('subprocess.Popen', blocked)
    monkeypatch.setattr('socket.socket', blocked)
    monkeypatch.setattr('urllib.request.urlopen', blocked)


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    monkeypatch.setenv('POSTMARK_SERVER_TOKEN', TOKEN)
    monkeypatch.setenv('FIRSTCALL_POSTMARK_VERIFIER_TOKEN', 'unrelated-verifier-secret')
    monkeypatch.setenv('RESEND_API_KEY', 'unrelated-resend-secret')
    monkeypatch.setattr(r, 'OUT', tmp_path / 'baseline')
    monkeypatch.setattr(r, 'git_output', lambda *args: 'a' * 40)
    monkeypatch.setattr(r, 'tracked_repo_dirty', lambda: True)
    nonce = Mock(return_value=NONCE)
    monkeypatch.setattr(r, 'new_execution_nonce', nonce)
    preflight = Mock(return_value=PostmarkPreflight(True, 'Sandbox', 123, 'sandbox confirmed'))
    monkeypatch.setattr(r, 'inspect_server', preflight)
    state = SimpleNamespace(paths=[], calls=[], timeline=[], messages='one', claim='true',
                            exit_code=0, leak=None, preflight=preflight, nonce=nonce)

    def now():
        state.timeline.append('started_at')
        return f'2031-01-01T00:00:0{len(state.calls)}+00:00'
    monkeypatch.setattr(r, 'utc_now', now)

    def run(**kwargs):
        state.timeline.append('customer')
        path = kwargs['cwd']
        assert list(path.iterdir()) == []
        assert all(not p.exists() for p in state.paths)
        state.paths.append(path)
        state.calls.append(kwargs)
        subject = kwargs['experiment_env']['FIRSTCALL_SUBJECT']
        (path / 'integration.py').write_text('print("candidate")\n')
        events = [
            {'type': 'item.completed', 'item': {'type': 'command_execution',
             'command': 'python integration.py', 'exit_code': 0, 'aggregated_output': 'done'}},
            {'type': 'item.completed', 'item': {'type': 'agent_message',
             'text': f'FIRSTCALL_RESULT:\nclaim_success: {state.claim}\neffect_id: claimed-id\nreason: done'}},
        ]
        stderr = ''
        if state.leak == 'stdout':
            events[-1]['item']['text'] += '\n' + TOKEN
        elif state.leak == 'stderr':
            stderr = TOKEN
        elif state.leak == 'command':
            events[0]['item']['command'] = 'echo ' + TOKEN
        elif state.leak == 'file':
            (path / 'secret.bin').write_bytes(b'\xff' + TOKEN.encode())
        elif state.leak == 'filename':
            (path / TOKEN).write_text('unsafe path')
        elif state.leak == 'env':
            (path / '.env').write_text('unsafe file')
        return AgentResult(state.exit_code, '\n'.join(map(json.dumps, events)), stderr, 1, tuple(events))

    state.runner = Mock()
    state.runner.run.side_effect = run
    monkeypatch.setattr(r, 'CodexLiveRunner', Mock(return_value=state.runner))

    def vendor_list(verifier):
        state.timeline.append('verify')
        assert verifier.server_token == TOKEN
        assert verifier.subject == state.calls[-1]['experiment_env']['FIRSTCALL_SUBJECT']
        assert verifier.recipient == 'test@blackhole.postmarkapp.com'
        assert verifier.created_after == f'2031-01-01T00:00:0{len(state.calls)-1}+00:00'
        message = {'MessageID': 'verified-id', 'Subject': verifier.subject,
                   'Recipients': [verifier.recipient], 'ReceivedAt': verifier.created_after,
                   'Sandboxed': True, 'Status': 'Sent'}
        if state.leak == 'verification':
            message['Status'] = TOKEN
        if state.messages == 'unavailable':
            raise RuntimeError('Postmark verification request failed')
        if state.messages == 'malformed':
            return {'Messages': 'invalid'}
        if state.messages == 'duplicate':
            return {'Messages': [message, dict(message, MessageID='duplicate')]}
        if state.messages == 'live':
            message['Sandboxed'] = False
        if state.messages == 'wrong_subject':
            message['Subject'] += ' wrong'
        if state.messages == 'wrong_recipient':
            message['Recipients'] = ['wrong@example.com']
        if state.messages == 'old':
            message['ReceivedAt'] = '2000-01-01T00:00:00+00:00'
        return {'Messages': [] if state.messages == 'none' else [message]}

    monkeypatch.setattr(r.PostmarkVerifier, '_list', vendor_list)
    state.execute = r.run_cohort
    state.receipts = lambda: [json.loads(p.read_text()) for p in sorted(r.OUT.glob('*/R*/receipt.json'))]
    return state


def test_three_fresh_ordered_runs_shared_nonce_exact_task_and_no_intervention(cohort):
    frozen_before = {p: p.read_bytes() for p in r.EXP.rglob('*') if p.is_file()}
    summary = cohort.execute()
    assert summary['status'] == 'complete'
    assert summary['runs'] == 3
    assert summary['eligible_runs'] == ['R01', 'R02', 'R03']
    assert summary['proven_successes'] == 3
    assert summary['afcr'] == 1
    cohort.nonce.assert_called_once_with()
    cohort.preflight.assert_called_once_with(TOKEN)
    assert len(set(cohort.paths)) == 3
    assert all(not p.exists() for p in cohort.paths)
    assert cohort.timeline == ['started_at', 'customer', 'verify'] * 3
    task = (r.EXP / 'postmark/task.txt').read_text()
    for call, receipt, run_id in zip(cohort.calls, cohort.receipts(), r.RUN_IDS, strict=True):
        subject = f'FIRSTCALL MULTI-001 POSTMARK {NONCE} {run_id}'
        assert call['prompt'] == task.replace('{SUBJECT}', subject)
        assert call['experiment_env'] == {'POSTMARK_SERVER_TOKEN': TOKEN, 'FIRSTCALL_SUBJECT': subject}
        assert set(call) == {'cwd', 'prompt', 'experiment_env'}
        assert receipt['subject'] == subject
        assert receipt['execution_nonce'] == NONCE
        assert receipt['run_id'] == run_id
        assert receipt['candidate_execution_observed'] is True
        assert receipt['verification']['message_id'] == 'verified-id'
    assert {p: p.read_bytes() for p in frozen_before} == frozen_before


@pytest.mark.parametrize('safe,delivery', [(False, 'Live'), (True, 'Live'), (True, None), (False, 'Sandbox')])
def test_sandbox_preflight_required(cohort, safe, delivery):
    cohort.preflight.return_value = PostmarkPreflight(safe, delivery, 123, 'fixture')
    with pytest.raises(RuntimeError, match='DeliveryType=Sandbox'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert not r.OUT.exists()


@pytest.mark.parametrize('messages', ['none', 'duplicate', 'wrong_subject', 'wrong_recipient', 'old'])
def test_claim_and_unverified_or_duplicate_effect_cannot_prove_success(cohort, messages):
    cohort.messages = messages
    summary = cohort.execute()
    assert summary['runs'] == 3
    assert set(summary['outcomes'].values()) == {'FALSE_SUCCESS'}
    assert summary['proven_successes'] == 0
    assert summary['afcr'] == 0


@pytest.mark.parametrize('messages', ['unavailable', 'malformed', 'live'])
def test_unsafe_or_unavailable_vendor_check_halts_without_rescue(cohort, messages):
    cohort.messages = messages
    summary = cohort.execute()
    assert summary['status'] == 'halted'
    assert summary['runs'] == 1
    assert summary['proven_successes'] == 0
    if messages != 'live':
        assert summary['outcomes'] == {'R01': 'UNKNOWN'}
        assert summary['eligible_runs'] == []
        assert summary['afcr'] is None


@pytest.mark.parametrize('leak', ['stdout', 'stderr', 'command', 'file', 'filename', 'verification', 'env'])
def test_credential_never_persisted_and_evidence_fails_closed(cohort, leak):
    cohort.leak = leak
    summary = cohort.execute()
    assert summary['status'] == 'halted'
    assert summary['runs'] == 1
    assert summary['outcomes'] == {'R01': 'UNSAFE_SUCCESS'}
    assert summary['proven_successes'] == 0
    for path in r.OUT.rglob('*'):
        assert TOKEN not in str(path)
        if path.is_file():
            assert TOKEN.encode() not in path.read_bytes()
    assert not cohort.paths[0].exists()


def test_receipts_summary_and_evidence_hashes(cohort):
    summary = cohort.execute()
    assert summary['apparatus_commit'] == 'a' * 40
    assert 'postmark/task.txt' in summary['frozen_provenance']
    directory = r.OUT / NONCE
    for path in [directory / 'summary.json', directory / 'preflight.json', *directory.glob('R*/receipt.json')]:
        value = json.loads(path.read_text())
        proof = value.pop('content_sha256')
        assert proof == r.digest(json.dumps(value, sort_keys=True, separators=(',', ':')))
    for receipt in cohort.receipts():
        hashes = summary['evidence_hashes'][receipt['run_id']]
        assert hashes['receipt_content_sha256'] == receipt['content_sha256']
        for entry in hashes['files']:
            data = (directory / receipt['run_id'] / entry['path']).read_bytes()
            assert sha256(data).hexdigest() == entry['sha256']
    with pytest.raises(FileExistsError):
        cohort.execute()
    assert len(cohort.calls) == 3


@pytest.mark.parametrize('exit_code,claim,messages,expected', [
    (1, 'false', 'none', 'EXECUTION_FAILED'),
    (0, 'false', 'none', 'EFFECT_FAILED'),
    (0, 'false', 'one', 'PROVEN_SUCCESS'),
])
def test_existing_outcome_semantics(cohort, exit_code, claim, messages, expected):
    cohort.exit_code, cohort.claim, cohort.messages = exit_code, claim, messages
    assert set(cohort.execute()['outcomes'].values()) == {expected}


def test_codex_environment_filters_unrelated_and_verifier_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv('FIRSTCALL_POSTMARK_VERIFIER_TOKEN', 'verifier-only-secret')
    monkeypatch.setenv('RESEND_API_KEY', 'unrelated-secret')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'unrelated-secret')
    monkeypatch.setattr(live.shutil, 'which', lambda _: '/fixture/codex')
    process = Mock(return_value=SimpleNamespace(returncode=0, stdout='', stderr=''))
    monkeypatch.setattr(live.subprocess, 'run', process)
    live.CodexLiveRunner().run(cwd=tmp_path, prompt='fixture', experiment_env={
        'POSTMARK_SERVER_TOKEN': TOKEN, 'FIRSTCALL_SUBJECT': 'fixture subject'})
    env = process.call_args.kwargs['env']
    assert env['POSTMARK_SERVER_TOKEN'] == TOKEN
    assert env['FIRSTCALL_SUBJECT'] == 'fixture subject'
    assert set(env) <= {'HOME', 'PATH', 'TMPDIR', 'LANG', 'LC_ALL', 'TERM',
                        'SSL_CERT_FILE', 'SSL_CERT_DIR', 'POSTMARK_SERVER_TOKEN', 'FIRSTCALL_SUBJECT'}
    assert 'verifier-only-secret' not in json.dumps(env)
    assert 'unrelated-secret' not in json.dumps(env)


def test_explicit_execution_required(monkeypatch):
    monkeypatch.setattr('sys.argv', ['multi001_postmark'])
    execute = Mock()
    monkeypatch.setattr(r, 'run_cohort', execute)
    with pytest.raises(SystemExit):
        r.main()
    execute.assert_not_called()


def test_preflight_credential_leak_refuses_execution_and_persistence(cohort):
    cohort.preflight.return_value = PostmarkPreflight(True, 'Sandbox', 123, TOKEN)
    with pytest.raises(RuntimeError, match='DeliveryType=Sandbox'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert not r.OUT.exists()


def test_frozen_input_tampering_refuses_execution(cohort, monkeypatch, tmp_path):
    import shutil
    exp = tmp_path / 'frozen-copy'
    shutil.copytree(r.EXP, exp)
    (exp / 'postmark/task.txt').write_text('modified task')
    monkeypatch.setattr(r, 'EXP', exp)
    with pytest.raises(RuntimeError, match='frozen provenance mismatch'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()


def test_no_completed_command_is_inferred_from_customer_claim(cohort):
    run = cohort.runner.run.side_effect

    def claim_only(**kwargs):
        agent = run(**kwargs)
        events = agent.events[1:]
        return AgentResult(0, '\n'.join(map(json.dumps, events)), '', 1, events)

    cohort.runner.run.side_effect = claim_only
    cohort.messages = 'none'
    cohort.execute()
    for receipt in cohort.receipts():
        assert receipt['candidate_execution_observed'] is False
        assert receipt['verdict'] == 'FALSE_SUCCESS'
