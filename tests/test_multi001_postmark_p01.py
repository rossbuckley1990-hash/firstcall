"""Mock-only cohort checks; subprocess and network are blocked in every test."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import secrets
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from firstcall.agents.codex_live import AgentResult
import firstcall.agents.codex_live as live
import firstcall.multi001_postmark_p01 as r
from firstcall.postmark_preflight import PostmarkPreflight

TOKEN = 'synthetic-postmark-credential'
NONCE = 'abcdef123456'
ONBOARDING_SHA256 = '8410998e0f53c0d56b8804fab215dce9955dbcb6a81d70b2bd88a39cee2ca4cc'
ONBOARDING_FILENAME = 'postmark-official-get-started.html'


@pytest.fixture(autouse=True)
def no_live_work(monkeypatch):
    blocked = Mock(side_effect=AssertionError('real processes/network forbidden'))
    monkeypatch.setattr('subprocess.run', blocked)
    monkeypatch.setattr('subprocess.Popen', blocked)
    monkeypatch.setattr('socket.socket', blocked)
    monkeypatch.setattr('urllib.request.urlopen', blocked)
    yield
    blocked.assert_not_called()


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    monkeypatch.setenv('POSTMARK_SERVER_TOKEN', TOKEN)
    sender = secrets.token_hex(16) + '@example.invalid'
    monkeypatch.setenv('POSTMARK_FROM', sender)
    monkeypatch.setenv('FIRSTCALL_POSTMARK_VERIFIER_TOKEN', 'unrelated-verifier-secret')
    monkeypatch.setenv('RESEND_API_KEY', 'unrelated-resend-secret')
    monkeypatch.setattr(r, 'OUT', tmp_path / 'p01-counterfactual')
    monkeypatch.setattr(r, 'git_output', lambda *args: 'a' * 40)
    monkeypatch.setattr(r, 'tracked_repo_dirty', lambda: True)
    nonce = Mock(return_value=NONCE)
    monkeypatch.setattr(r, 'new_execution_nonce', nonce)
    def inspect(token):
        assert token == TOKEN
        assert 'POSTMARK_FROM' not in os.environ
        state.timeline.append('preflight')
        return PostmarkPreflight(True, 'Sandbox', 123, 'sandbox confirmed')

    preflight = Mock(side_effect=inspect)
    monkeypatch.setattr(r, 'inspect_server', preflight)
    state = SimpleNamespace(paths=[], workspaces=[], supplied=[], calls=[], timeline=[],
                            messages='one', claim='true', sender=sender, leak_value=TOKEN,
                            exit_code=0, leak=None, preflight=preflight, nonce=nonce)
    frozen_onboarding = (r.EXP / 'postmark/official-onboarding/get-started.html').read_bytes()
    create_workspace = r.create_workspace

    def fresh_workspace():
        workspace = create_workspace()
        assert list(workspace.path.iterdir()) == []
        state.workspaces.append(workspace.path)
        return workspace

    monkeypatch.setattr(r, 'create_workspace', fresh_workspace)

    def now():
        state.timeline.append('started_at')
        return f'2031-01-01T00:00:0{len(state.calls)}+00:00'
    monkeypatch.setattr(r, 'utc_now', now)

    def cohort_env_absent():
        return 'POSTMARK_FROM' not in os.environ

    def run(**kwargs):
        state.timeline.append('customer')
        path = kwargs['cwd']
        assert cohort_env_absent()
        assert kwargs['experiment_env']['POSTMARK_FROM'] == state.sender
        assert list(path.iterdir()) == [path / ONBOARDING_FILENAME]
        supplied = (path / ONBOARDING_FILENAME).read_bytes()
        assert supplied == frozen_onboarding
        assert sha256(supplied).hexdigest() == ONBOARDING_SHA256
        state.supplied.append(supplied)
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
            events[-1]['item']['text'] += '\n' + state.leak_value
        elif state.leak == 'stderr':
            stderr = state.leak_value
        elif state.leak == 'command':
            events[0]['item']['command'] = 'echo ' + state.leak_value
        elif state.leak == 'file':
            (path / 'secret.bin').write_bytes(b'\xff' + state.leak_value.encode())
        elif state.leak == 'filename':
            (path / state.leak_value).write_text('unsafe path')
        elif state.leak == 'env':
            (path / '.env').write_text('unsafe file')
        return AgentResult(state.exit_code, '\n'.join(map(json.dumps, events)), stderr, 1, tuple(events))

    state.runner = Mock()
    state.runner.run.side_effect = run
    monkeypatch.setattr(r, 'CodexLiveRunner', Mock(return_value=state.runner))

    def vendor_list(verifier):
        assert 'POSTMARK_FROM' not in os.environ
        assert state.sender not in vars(verifier).values()
        state.timeline.append('verify')
        assert verifier.server_token == TOKEN
        assert verifier.subject == state.calls[-1]['experiment_env']['FIRSTCALL_SUBJECT']
        assert verifier.recipient == 'test@blackhole.postmarkapp.com'
        assert verifier.created_after == f'2031-01-01T00:00:0{len(state.calls)-1}+00:00'
        message = {'MessageID': 'verified-id', 'Subject': verifier.subject,
                   'Recipients': [verifier.recipient], 'ReceivedAt': verifier.created_after,
                   'Sandboxed': True, 'Status': 'Sent'}
        if state.leak == 'verification':
            message['Status'] = state.leak_value
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
    state.receipts = lambda: [json.loads(p.read_text()) for p in sorted(r.OUT.glob('*/P01-R*/receipt.json'))]
    return state


def test_three_fresh_ordered_runs_shared_nonce_exact_task_and_no_intervention(cohort):
    frozen_before = {p: p.read_bytes() for p in r.EXP.rglob('*') if p.is_file()}
    summary = cohort.execute()
    assert summary['status'] == 'complete'
    assert summary['runs'] == 3
    assert summary['eligible_runs'] == ['P01-R01', 'P01-R02', 'P01-R03']
    assert summary['proven_successes'] == 3
    assert summary['afcr'] == 1
    cohort.nonce.assert_called_once_with()
    cohort.preflight.assert_called_once_with(TOKEN)
    assert len(set(cohort.paths)) == 3
    assert all(not p.exists() for p in cohort.paths)
    assert cohort.timeline == ['preflight'] + ['started_at', 'customer', 'verify'] * 3
    task = (r.EXP / 'postmark/task.txt').read_text()
    for call, receipt, run_id in zip(cohort.calls, cohort.receipts(), r.RUN_IDS, strict=True):
        subject = f'FIRSTCALL MULTI-001 POSTMARK {NONCE} {run_id}'
        assert call['prompt'] == task.replace('{SUBJECT}', subject)
        assert call['experiment_env'] == {'POSTMARK_SERVER_TOKEN': TOKEN, 'POSTMARK_FROM': cohort.sender, 'FIRSTCALL_SUBJECT': subject}
        assert set(call) == {'cwd', 'prompt', 'experiment_env'}
        assert receipt['subject'] == subject
        assert receipt['execution_nonce'] == NONCE
        assert receipt['run_id'] == run_id
        assert receipt['candidate_execution_observed'] is True
        assert receipt['verification']['message_id'] == 'verified-id'
    assert {p: p.read_bytes() for p in frozen_before} == frozen_before


def test_onboarding_source_hash_is_pinned():
    source = r.EXP / 'postmark/official-onboarding/get-started.html'
    manifest = json.loads(source.with_name('manifest.json').read_bytes())
    assert r.ONBOARDING_SHA256 == ONBOARDING_SHA256
    assert r.ONBOARDING_FILENAME == ONBOARDING_FILENAME
    assert sha256(source.read_bytes()).hexdigest() == ONBOARDING_SHA256
    assert manifest['sha256'] == ONBOARDING_SHA256
    assert len(source.read_bytes()) == manifest['bytes']


def test_same_exact_onboarding_bytes_delivered_and_captured_for_each_run(cohort):
    frozen = (r.EXP / 'postmark/official-onboarding/get-started.html').read_bytes()
    summary = cohort.execute()
    assert cohort.supplied == [frozen] * 3
    for run_id in r.RUN_IDS:
        directory = r.OUT / NONCE / run_id
        relative = 'workspace/' + ONBOARDING_FILENAME
        assert (directory / relative).read_bytes() == frozen
        manifest = json.loads((directory / 'workspace-manifest.json').read_bytes())
        entry = next(item for item in manifest if item['path'] == ONBOARDING_FILENAME)
        assert entry['sha256'] == entry['persisted_sha256'] == ONBOARDING_SHA256
        assert entry['bytes'] == entry['persisted_bytes'] == len(frozen)
        evidence = summary['evidence_hashes'][run_id]['files']
        assert next(item for item in evidence if item['path'] == relative)['sha256'] == ONBOARDING_SHA256


@pytest.mark.parametrize('failed_run', [1, 2, 3])
@pytest.mark.parametrize('corruption', ['source', 'workspace'])
def test_onboarding_hash_mismatch_fails_closed_before_affected_customer(
    cohort, monkeypatch, tmp_path, failed_run, corruption,
):
    exp = tmp_path / 'frozen-copy'
    shutil.copytree(r.EXP, exp)
    monkeypatch.setattr(r, 'EXP', exp)
    source = exp / 'postmark/official-onboarding/get-started.html'
    create_workspace = r.create_workspace
    write_bytes = Path.write_bytes

    def fresh_workspace():
        workspace = create_workspace()
        if corruption == 'source' and len(cohort.workspaces) == failed_run:
            source.write_bytes(source.read_bytes() + b'\n')
        return workspace

    def corrupt_copy(path, data):
        if (corruption == 'workspace' and path.name == ONBOARDING_FILENAME
                and len(cohort.workspaces) == failed_run):
            data += b'\n'
        return write_bytes(path, data)

    monkeypatch.setattr(r, 'create_workspace', fresh_workspace)
    monkeypatch.setattr(Path, 'write_bytes', corrupt_copy)
    with pytest.raises(RuntimeError, match=f'official onboarding {corruption} SHA256 mismatch'):
        cohort.execute()
    assert cohort.runner.run.call_count == failed_run - 1
    assert cohort.timeline == ['preflight'] + ['started_at', 'customer', 'verify'] * (failed_run - 1)
    assert len(cohort.workspaces) == failed_run
    assert all(not path.exists() for path in cohort.workspaces)
    assert not (r.OUT / NONCE / f'P01-R{failed_run:02d}').exists()
    assert not (r.OUT / NONCE / 'summary.json').exists()


@pytest.mark.parametrize('safe,delivery', [(False, 'Live'), (True, 'Live'), (True, None), (False, 'Sandbox')])
def test_sandbox_preflight_required(cohort, safe, delivery):
    cohort.preflight.side_effect = None
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
        assert summary['outcomes'] == {'P01-R01': 'UNKNOWN'}
        assert summary['eligible_runs'] == []
        assert summary['afcr'] is None


@pytest.mark.parametrize('leak', ['stdout', 'stderr', 'command', 'file', 'filename', 'verification', 'env'])
def test_credential_never_persisted_and_evidence_fails_closed(cohort, leak):
    cohort.leak = leak
    summary = cohort.execute()
    assert summary['status'] == 'halted'
    assert summary['runs'] == 1
    assert summary['outcomes'] == {'P01-R01': 'UNSAFE_SUCCESS'}
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
    for path in [directory / 'summary.json', directory / 'preflight.json', *directory.glob('P01-R*/receipt.json')]:
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
    sender = secrets.token_hex(16) + '@example.invalid'
    live.CodexLiveRunner().run(cwd=tmp_path, prompt='fixture', experiment_env={
        'POSTMARK_SERVER_TOKEN': TOKEN, 'POSTMARK_FROM': sender, 'FIRSTCALL_SUBJECT': 'fixture subject'})
    env = process.call_args.kwargs['env']
    assert env['POSTMARK_FROM'] == sender
    assert sender not in json.dumps(process.call_args.args)
    assert env['POSTMARK_SERVER_TOKEN'] == TOKEN
    assert env['FIRSTCALL_SUBJECT'] == 'fixture subject'
    assert set(env) <= {'HOME', 'PATH', 'TMPDIR', 'LANG', 'LC_ALL', 'TERM',
                        'SSL_CERT_FILE', 'SSL_CERT_DIR', 'POSTMARK_SERVER_TOKEN', 'POSTMARK_FROM', 'FIRSTCALL_SUBJECT'}
    assert 'verifier-only-secret' not in json.dumps(env)
    assert 'unrelated-secret' not in json.dumps(env)


def test_explicit_execution_required(monkeypatch):
    monkeypatch.setattr('sys.argv', ['multi001_postmark_p01'])
    execute = Mock()
    monkeypatch.setattr(r, 'run_cohort', execute)
    with pytest.raises(SystemExit):
        r.main()
    execute.assert_not_called()


def test_preflight_credential_leak_refuses_execution_and_persistence(cohort):
    cohort.preflight.side_effect = None
    cohort.preflight.return_value = PostmarkPreflight(True, 'Sandbox', 123, TOKEN)
    with pytest.raises(RuntimeError, match='DeliveryType=Sandbox'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert not r.OUT.exists()


def test_frozen_input_tampering_refuses_execution(cohort, monkeypatch, tmp_path):
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


@pytest.mark.parametrize('name', ['POSTMARK_SERVER_TOKEN', 'POSTMARK_FROM'])
@pytest.mark.parametrize('value', [None, ''])
def test_required_environment_fails_before_any_work(cohort, monkeypatch, name, value):
    if value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match=name + ' is required'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()
    cohort.nonce.assert_not_called()
    assert not r.OUT.exists()


@pytest.mark.parametrize('leak', ['stdout', 'stderr', 'command', 'file', 'filename', 'verification'])
@pytest.mark.parametrize('escaped', [False, True])
def test_sender_never_printed_or_persisted(cohort, monkeypatch, capsys, leak, escaped):
    if escaped:
        cohort.sender = '"Synthetic \\ Sender" <' + secrets.token_hex(16) + '@example.invalid>'
        monkeypatch.setenv('POSTMARK_FROM', cohort.sender)
    cohort.leak, cohort.leak_value = leak, cohort.sender
    summary = cohort.execute()
    assert summary['status'] == 'halted'
    assert summary['runs'] == 1
    assert summary['proven_successes'] == 0
    assert summary['sender_sha256'] == sha256(cohort.sender.encode()).hexdigest()
    assert summary['evidence_integrity']['status'] == 'redacted'
    needles = [cohort.sender.encode(), json.dumps(cohort.sender)[1:-1].encode()]
    for path in r.OUT.rglob('*'):
        assert all(needle not in str(path).encode() for needle in needles)
        if path.is_file():
            assert all(needle not in path.read_bytes() for needle in needles)
    captured = capsys.readouterr()
    assert cohort.sender not in captured.out + captured.err
    assert os.environ['POSTMARK_FROM'] == cohort.sender


def test_sender_is_read_at_execution_time_without_hardcoded_default(cohort, monkeypatch):
    cohort.execute()
    replacement = secrets.token_hex(16) + '@example.invalid'
    cohort.sender = replacement
    monkeypatch.setenv('POSTMARK_FROM', replacement)
    cohort.nonce.return_value = 'fedcba654321'
    summary = cohort.execute()
    assert len(cohort.calls) == 6
    assert all(call['experiment_env']['POSTMARK_FROM'] == replacement for call in cohort.calls[3:])
    assert summary['sender_sha256'] == sha256(replacement.encode()).hexdigest()


def test_summary_identifies_frozen_diagnosis_baseline_and_p01(cohort):
    summary = cohort.execute()
    assert summary['experiment'] == 'MULTI-001'
    assert summary['product'] == 'POSTMARK'
    assert summary['phase'] == summary['stage'] == 'P01_COUNTERFACTUAL'
    assert summary['diagnosis_commit'] == '530351d120bac32b066aa70cbf8646387668cdac'
    assert summary['diagnosis_tag'] == 'multi-001-postmark-p01-diagnosis'
    assert summary['diagnosis_sha256'] == '8e3669969f77db0fbb39d51d3e38e05748a7576b8194ef8c2e6d5479b4543df3'
    assert summary['baseline_cohort'] == 'd0bd8c7ade2b'
    assert summary['baseline_afcr'] == {'proven_successes': 0, 'eligible_runs': 3, 'afcr': 0.0}
    assert summary['onboarding_sha256'] == ONBOARDING_SHA256
    assert summary['execution_nonce'] == NONCE
    assert summary['planned_runs'] == ['P01-R01', 'P01-R02', 'P01-R03']
    assert summary['runner_sha256'] == sha256(Path(r.__file__).read_bytes()).hexdigest()


def test_diagnosis_tampering_fails_before_preflight(cohort, monkeypatch, tmp_path):
    exp = tmp_path / 'frozen-copy'
    shutil.copytree(r.EXP, exp)
    monkeypatch.setattr(r, 'EXP', exp)
    diagnosis = exp / 'postmark/diagnoses/p01.json'
    diagnosis.write_bytes(diagnosis.read_bytes() + b'\n')
    with pytest.raises(RuntimeError, match='frozen diagnosis SHA256 mismatch'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()
    assert os.environ['POSTMARK_FROM'] == cohort.sender
    assert not r.OUT.exists()


def test_started_command_and_prose_are_not_execution_proof(cohort):
    run = cohort.runner.run.side_effect

    def incomplete(**kwargs):
        agent = run(**kwargs)
        command = dict(agent.events[0], type='item.started')
        events = (command, agent.events[1])
        return AgentResult(0, '\n'.join(map(json.dumps, events)), '', 1, events)

    cohort.runner.run.side_effect = incomplete
    cohort.execute()
    for receipt in cohort.receipts():
        assert receipt['candidate_execution_observed'] is False
        assert receipt['candidate_commands'] == []


def test_ambiguous_customer_failure_is_not_retried(cohort):
    cohort.runner.run.side_effect = RuntimeError(cohort.sender)
    # An unavailable vendor check cannot resolve an ambiguous execution.
    cohort.messages = 'unavailable'
    # No customer fixture completed, so mock only the vendor transport here.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(r.PostmarkVerifier, '_list', Mock(side_effect=RuntimeError(
            'Postmark verification request failed')))
        summary = cohort.execute()
    cohort.runner.run.assert_called_once()
    assert summary['status'] == 'halted'
    assert summary['eligible_runs'] == []
    assert summary['outcomes'] == {'P01-R01': 'UNKNOWN'}
    assert cohort.sender not in json.dumps(summary)


def test_preflight_sender_leak_fails_without_persistence(cohort):
    cohort.preflight.side_effect = None
    cohort.preflight.return_value = PostmarkPreflight(True, 'Sandbox', 123, cohort.sender)
    with pytest.raises(RuntimeError, match='DeliveryType=Sandbox'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert os.environ['POSTMARK_FROM'] == cohort.sender
    assert not r.OUT.exists()


@pytest.mark.parametrize('nonce', ['', 'invalid', 'a' * 13])
def test_invalid_nonce_fails_before_customer(cohort, nonce):
    cohort.nonce.return_value = nonce
    with pytest.raises(ValueError, match='invalid execution nonce'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert not r.OUT.exists()


def tree_digest(root):
    entries = {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
               for p in sorted(root.rglob('*')) if p.is_file()}
    return sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def test_frozen_files_and_historical_baseline_evidence_untouched(cohort):
    # Pinned from diagnosis commit 530351d, including both baseline cohorts.
    protected = {
        'artifacts/multi-001/postmark/baseline': '40289fdcf64dc5c8073ed90b22a698cd6897d9a7fc118fa51c6e5add8d9087f7',
        'experiments/multi-001': '498c911d09bb37daf595f6df39a8d260b84ff1e24c2d07074a2ba4d393ba87a5',
    }
    for relative, expected in protected.items():
        assert tree_digest(r.ROOT / relative) == expected
    cohort.execute()
    for relative, expected in protected.items():
        assert tree_digest(r.ROOT / relative) == expected


@pytest.mark.parametrize('relative,expected', [
    ('firstcall/multi001_postmark.py', '47557898ff255d8d244971194a51ff8b1cf4494b851affea1f6832c373e705e3'),
    ('firstcall/verifiers/postmark.py', '7ac6b91fc78190e566e887e7bfaf6e105b049f676919c77e4b81eaa350ef9cf6'),
    ('firstcall/postmark_preflight.py', '967f92f90dc49cb87ed52056d14e32203624fffc0cfa81dbbcc63ee547570ddc'),
    ('firstcall/agents/codex_live.py', '1265f353e531c7940e09203ea6a63e5ed76d63a4a9da79ee3f1a7cc84b2c79e0'),
    ('firstcall/agents/codex_events.py', 'c61e063a85499e2a46b26df4e4d580590bf43aab8fa2b5edcb9500a297f2eb9c'),
    ('firstcall/grade.py', '4ba7304bc5f1ffa79f4500cfc0145c7cabb5535842bee5cff6ba9e3bc0e72244'),
])
def test_baseline_apparatus_semantics_unchanged(relative, expected):
    assert sha256((r.ROOT / relative).read_bytes()).hexdigest() == expected


def test_p01_output_cannot_rewrite_baseline():
    assert r.OUT == r.ROOT / 'artifacts/multi-001/postmark/p01-counterfactual'
