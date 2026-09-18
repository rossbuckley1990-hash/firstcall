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
import firstcall.multi001_postmark_p02 as r
from firstcall.postmark_preflight import PostmarkPreflight

TOKEN = 'synthetic-postmark-credential'
NONCE = 'abcdef123456'
ONBOARDING_SHA256 = '823dbea537294f9fd89a18ed779f50be4eeea423dac5da366c991fdf841555af'
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
    # The production P02 manifest MUST reject the repaired apparatus. Exercise
    # mock-only runner flow using an explicitly separate, temporary test manifest.
    # Never repin the historical manifest, receipts, or production constants.
    test_exp = tmp_path / 'mock-p02-inputs'
    shutil.copytree(r.P02_EXP, test_exp)
    manifest_path = test_exp / 'manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    for name in ('firstcall/verifiers/postmark.py', 'tests/test_multi001_postmark_p01.py'):
        data = (r.ROOT / name).read_bytes()
        manifest['files'][name] = {'bytes': len(data), 'sha256': sha256(data).hexdigest()}
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr(r, 'P02_EXP', test_exp)
    monkeypatch.setattr(r, 'P02_MANIFEST_SHA256', sha256(manifest_path.read_bytes()).hexdigest())
    monkeypatch.setenv('POSTMARK_SERVER_TOKEN', TOKEN)
    sender = secrets.token_hex(16) + '@example.invalid'
    monkeypatch.setenv('POSTMARK_FROM', sender)
    monkeypatch.setenv('FIRSTCALL_POSTMARK_VERIFIER_TOKEN', 'unrelated-verifier-secret')
    monkeypatch.setenv('RESEND_API_KEY', 'unrelated-resend-secret')
    monkeypatch.setattr(r, 'OUT', tmp_path / 'p02-counterfactual')
    monkeypatch.setattr(r, 'OUTPUT_ROOT', r.OUT)
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
    frozen_onboarding = (r.P02_EXP / 'get-started.html').read_bytes()
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
    state.receipts = lambda: [json.loads(p.read_text()) for p in sorted(r.OUT.glob('*/P02-R*/receipt.json'))]
    return state


def test_three_fresh_ordered_runs_shared_nonce_exact_task_and_environment(cohort):
    frozen_before = {p: p.read_bytes() for p in r.EXP.rglob('*') if p.is_file()}
    summary = cohort.execute()
    assert summary['status'] == 'complete'
    assert summary['runs'] == 3
    assert summary['eligible_runs'] == ['P02-R01', 'P02-R02', 'P02-R03']
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
    source = r.P02_EXP / 'get-started.html'
    manifest = json.loads(source.with_name('manifest.json').read_bytes())
    assert r.ONBOARDING_SHA256 == ONBOARDING_SHA256
    assert r.ONBOARDING_FILENAME == ONBOARDING_FILENAME
    assert sha256(source.read_bytes()).hexdigest() == ONBOARDING_SHA256
    entry = manifest['files']['experiments/multi-001-postmark-p02/get-started.html']
    assert entry['sha256'] == ONBOARDING_SHA256
    assert len(source.read_bytes()) == entry['bytes']


def test_same_exact_onboarding_bytes_delivered_and_captured_for_each_run(cohort):
    frozen = (r.P02_EXP / 'get-started.html').read_bytes()
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
    p02_exp = tmp_path / 'p02-copy'
    shutil.copytree(r.P02_EXP, p02_exp)
    monkeypatch.setattr(r, 'P02_EXP', p02_exp)
    source = p02_exp / 'get-started.html'
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
    assert not (r.OUT / NONCE / f'P02-R{failed_run:02d}').exists()
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
        assert summary['outcomes'] == {'P02-R01': 'UNKNOWN'}
        assert summary['eligible_runs'] == []
        assert summary['afcr'] is None


@pytest.mark.parametrize('leak', ['stdout', 'stderr', 'command', 'file', 'filename', 'verification', 'env'])
def test_credential_never_persisted_and_evidence_fails_closed(cohort, leak):
    cohort.leak = leak
    summary = cohort.execute()
    assert summary['status'] == 'halted'
    assert summary['runs'] == 1
    assert summary['outcomes'] == {'P02-R01': 'UNSAFE_SUCCESS'}
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
    for path in [directory / 'summary.json', directory / 'preflight.json', *directory.glob('P02-R*/receipt.json')]:
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
    monkeypatch.setattr('sys.argv', ['multi001_postmark_p02'])
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


def test_summary_identifies_frozen_baseline_p01_and_p02(cohort):
    summary = cohort.execute()
    assert summary['experiment'] == 'MULTI-001'
    assert summary['product'] == 'POSTMARK'
    assert summary['phase'] == summary['stage'] == 'P02_COUNTERFACTUAL'
    assert summary['frozen_p01']['commit'] == '9015c333080c4e192d680d6f88ce9360d74353c5'
    assert summary['frozen_p01']['apparatus_tag'] == 'multi-001-postmark-p01-apparatus'
    assert summary['frozen_p01']['diagnosis_tag'] == 'multi-001-postmark-p01-diagnosis'
    assert summary['frozen_p01']['canonical_evidence'].endswith('/ca116baa8519')
    assert summary['frozen_baseline']['commit'] == 'ce95ed52ec9b728d43d8247ef3f2df53fee61ab1'
    assert summary['baseline_cohort'] == 'd0bd8c7ade2b'
    assert summary['baseline_afcr'] == {'proven_successes': 0, 'eligible_runs': 3, 'afcr': 0.0}
    assert summary['diagnosis_sha256'] == r.P02_DIAGNOSIS_SHA256
    assert summary['p02_manifest_sha256'] == r.P02_MANIFEST_SHA256
    assert summary['diagnosis'] == json.loads((r.P02_EXP / 'diagnosis.json').read_bytes())
    assert summary['onboarding_sha256'] == ONBOARDING_SHA256
    assert summary['execution_nonce'] == NONCE
    assert summary['planned_runs'] == ['P02-R01', 'P02-R02', 'P02-R03']
    assert summary['runner_sha256'] == sha256(Path(r.__file__).read_bytes()).hexdigest()
    for receipt in cohort.receipts():
        for key in ['diagnosis', 'diagnosis_sha256', 'p02_manifest_sha256',
                    'frozen_p01', 'frozen_baseline', 'onboarding_sha256', 'phase']:
            assert receipt[key] == summary[key]


def test_diagnosis_tampering_fails_before_preflight(cohort, monkeypatch, tmp_path):
    exp = tmp_path / 'frozen-copy'
    shutil.copytree(r.P02_EXP, exp)
    monkeypatch.setattr(r, 'P02_EXP', exp)
    diagnosis = exp / 'diagnosis.json'
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
    assert summary['outcomes'] == {'P02-R01': 'UNKNOWN'}
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
        'artifacts/multi-001/postmark/p01-counterfactual': '5657700e9b74388c6b8cebe7b0c7b3c3210267b7ad5e82ff5ec0b1eb0cacfcc6',
        'artifacts/multi-001/postmark/p01-counterfactual/ca116baa8519': '6a975b16d84227d7cd5c23372f02fe43e3d167f6c68ea2a262f696f7b7989e34',
    }
    for relative, expected in protected.items():
        assert tree_digest(r.ROOT / relative) == expected
    cohort.execute()
    for relative, expected in protected.items():
        assert tree_digest(r.ROOT / relative) == expected


@pytest.mark.parametrize('relative,expected', [
    ('firstcall/multi001_postmark_p01.py', '55e1c3d05ead64847dea14e71d52d090230e017ae1bfce63078b57d41dd520b3'),
    ('docs/multi001-postmark-p01.md', '803c2b669216b91c4a144330cf23c89cf01a9311168e3d0db8642972ec405d5d'),

    ('firstcall/multi001_postmark.py', '47557898ff255d8d244971194a51ff8b1cf4494b851affea1f6832c373e705e3'),
    ('firstcall/postmark_preflight.py', '967f92f90dc49cb87ed52056d14e32203624fffc0cfa81dbbcc63ee547570ddc'),
    ('firstcall/agents/codex_live.py', '1265f353e531c7940e09203ea6a63e5ed76d63a4a9da79ee3f1a7cc84b2c79e0'),
    ('firstcall/agents/codex_events.py', 'c61e063a85499e2a46b26df4e4d580590bf43aab8fa2b5edcb9500a297f2eb9c'),
    ('firstcall/grade.py', '4ba7304bc5f1ffa79f4500cfc0145c7cabb5535842bee5cff6ba9e3bc0e72244'),
])
def test_baseline_apparatus_semantics_unchanged(relative, expected):
    assert sha256((r.ROOT / relative).read_bytes()).hexdigest() == expected


def test_p02_output_has_dedicated_default():
    assert r.OUT == r.ROOT / 'artifacts/multi-001/postmark/p02-counterfactual'


def test_only_customer_facing_delta_is_exact_discoverability_paragraph(cohort):
    original = (r.EXP / 'postmark/official-onboarding/get-started.html').read_bytes()
    addition = (b'\n<p>A concrete verified sender identity is available in the '
                b'environment variable POSTMARK_FROM.</p>')
    anchor = b'<body id="api" class="docs-modern">'
    supplied = (r.P02_EXP / 'get-started.html').read_bytes()
    assert original.count(anchor) == 1
    assert supplied == original.replace(anchor, anchor + addition, 1)
    assert supplied.count(addition) == 1
    assert supplied.replace(addition, b'', 1) == original
    assert cohort.sender.encode() not in supplied
    cohort.execute()
    assert cohort.supplied == [supplied] * 3
    for call, receipt in zip(cohort.calls, cohort.receipts(), strict=True):
        assert r.INTERVENTION not in call['prompt']
        assert cohort.sender not in call['prompt']
        assert receipt['controls']['firstcall_rescue'] is False
        assert receipt['controls']['sandboxed_effect_required'] is True


def test_prediction_is_frozen_before_execution_and_never_rewritten(cohort):
    before = {p: p.read_bytes() for p in r.P02_EXP.iterdir() if p.is_file()}
    diagnosis = json.loads((r.P02_EXP / 'diagnosis.json').read_bytes())
    assert diagnosis['diagnosis_status'] == 'FROZEN_BEFORE_EXECUTION'
    assert diagnosis['real_runs_executed_at_freeze'] == 0
    assert diagnosis['prediction'] == (
        'Fresh autonomous customers should progress beyond MissingFromAddress. '
        'Making the already-supplied sender identity discoverable through '
        'POSTMARK_FROM is not predicted to guarantee a successful effect.')
    assert sha256((r.P02_EXP / 'manifest.json').read_bytes()).hexdigest() == r.P02_MANIFEST_SHA256
    assert sha256((r.P02_EXP / 'diagnosis.json').read_bytes()).hexdigest() == r.P02_DIAGNOSIS_SHA256
    cohort.execute()
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize('filename', ['manifest.json', 'get-started.html'])
def test_p02_tampering_rejected_before_preflight(cohort, tmp_path, monkeypatch, filename):
    exp = tmp_path / 'p02-copy'
    shutil.copytree(r.P02_EXP, exp)
    monkeypatch.setattr(r, 'P02_EXP', exp)
    path = exp / filename
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(RuntimeError, match='mismatch'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()
    assert not r.OUT.exists()


@pytest.mark.parametrize('filename', ['postmark/subject-contract.json',
                                      'postmark/policy.json',
                                      'postmark/apparatus-manifest.json'])
def test_original_contract_and_manifest_tampering_rejected(cohort, tmp_path, monkeypatch, filename):
    exp = tmp_path / 'original-copy'
    shutil.copytree(r.EXP, exp)
    monkeypatch.setattr(r, 'EXP', exp)
    path = exp / filename
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(RuntimeError, match='frozen provenance mismatch'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()


@pytest.mark.parametrize('after_run', [1, 3])
def test_mid_cohort_prediction_tampering_cannot_change_record(cohort, tmp_path, monkeypatch, after_run):
    exp = tmp_path / 'p02-copy'
    shutil.copytree(r.P02_EXP, exp)
    monkeypatch.setattr(r, 'P02_EXP', exp)
    run = cohort.runner.run.side_effect

    def tamper(**kwargs):
        agent = run(**kwargs)
        if len(cohort.calls) == after_run:
            path = exp / 'diagnosis.json'
            path.write_bytes(path.read_bytes() + b'\n')
        return agent

    cohort.runner.run.side_effect = tamper
    with pytest.raises(RuntimeError, match='frozen diagnosis SHA256 mismatch'):
        cohort.execute()
    assert cohort.runner.run.call_count == after_run
    assert not (r.OUT / NONCE / 'summary.json').exists()
    for receipt in cohort.receipts():
        assert receipt['diagnosis_sha256'] == r.P02_DIAGNOSIS_SHA256
    assert all(not path.exists() for path in cohort.paths)


@pytest.mark.parametrize('protected', ['baseline', 'p01-counterfactual',
                                      'p01-counterfactual/ca116baa8519'])
def test_output_redirection_to_protected_roots_fails_before_work(cohort, monkeypatch, protected):
    monkeypatch.setattr(r, 'OUT', r.ROOT / 'artifacts/multi-001/postmark' / protected)
    with pytest.raises(RuntimeError, match='dedicated artifact root'):
        cohort.execute()
    cohort.preflight.assert_not_called()
    cohort.runner.run.assert_not_called()


@pytest.mark.parametrize('location', ['root', 'ancestor', 'nonce'])
def test_output_symlink_redirection_fails_closed(cohort, tmp_path, monkeypatch, location):
    target = tmp_path / 'protected'
    target.mkdir()
    if location == 'root':
        r.OUT.symlink_to(target, target_is_directory=True)
    elif location == 'ancestor':
        alias = tmp_path / 'alias'
        alias.symlink_to(target, target_is_directory=True)
        monkeypatch.setattr(r, 'OUT', alias / 'p02-counterfactual')
        monkeypatch.setattr(r, 'OUTPUT_ROOT', r.OUT)
    else:
        r.OUT.mkdir()
        (r.OUT / NONCE).symlink_to(target, target_is_directory=True)
    with pytest.raises(RuntimeError, match='dedicated artifact root'):
        cohort.execute()
    cohort.runner.run.assert_not_called()
    assert list(target.iterdir()) == []


def test_direct_persistence_cannot_escape_output_root(cohort, tmp_path):
    with pytest.raises(RuntimeError, match='dedicated artifact root'):
        r.persist(tmp_path / 'receipt.json', {}, r.EvidenceSafety(TOKEN, cohort.sender))
    assert not (tmp_path / 'receipt.json').exists()


def test_p01_execution_and_grading_flow_is_mechanically_preserved():
    import ast
    p01 = ast.parse((r.ROOT / 'firstcall/multi001_postmark_p01.py').read_text())
    p02 = ast.parse(Path(r.__file__).read_text())
    functions = lambda module: {node.name: node for node in module.body
                               if isinstance(node, ast.FunctionDef)}
    old, new = functions(p01), functions(p02)
    for name in ['customer_claim', 'run_cohort', 'main']:
        assert ast.dump(old[name]) == ast.dump(new[name])
    # All code from customer launch through grading, halts and cleanup is
    # byte-identical except the harness-only intervention label.
    original = ast.get_source_segment((r.ROOT / 'firstcall/multi001_postmark_p01.py').read_text(), old['run_one'])
    derived = ast.get_source_segment(Path(r.__file__).read_text(), new['run_one'])
    marker = '        started_at = utc_now()'
    assert derived[derived.index(marker):].replace(
        "'POSTMARK_FROM discoverability'", "'POSTMARK_FROM'") == original[original.index(marker):]


def test_production_p02_manifest_rejects_repaired_apparatus_before_live_work():
    # No cohort is executed: validate the actual, immutable production pins.
    with pytest.raises(RuntimeError, match='frozen provenance mismatch'):
        r.validate_p02_inputs()


def test_historical_p02_verifier_and_afcr_remain_frozen():
    manifest = json.loads((r.P02_EXP / 'manifest.json').read_bytes())
    expected = '7ac6b91fc78190e566e887e7bfaf6e105b049f676919c77e4b81eaa350ef9cf6'
    assert manifest['files']['firstcall/verifiers/postmark.py']['sha256'] == expected
    assert manifest['files']['tests/test_multi001_postmark_p01.py']['sha256'] == (
        '993b4c94cbb489a3811fc37fdd54f3e8dc3c605c45618de3d013a917e165fea0')
    root = r.ROOT / 'artifacts/multi-001/postmark/p02-counterfactual/9906c79fc405'
    summary = json.loads((root / 'summary.json').read_bytes())
    assert summary['proven_successes'] == 2
    assert len(summary['eligible_runs']) == 3
    assert summary['afcr'] == 2 / 3
    for run in r.RUN_IDS:
        receipt = json.loads((root / run / 'receipt.json').read_bytes())
        assert receipt['apparatus_files']['firstcall/verifiers/postmark.py'] == expected
    r02 = json.loads((root / 'P02-R02/receipt.json').read_bytes())
    assert r02['verdict'] == 'FALSE_SUCCESS'
    assert r02['verification']['observed'] is False
    assert r02['verification']['reason'] == 'vendor effect not observed'
