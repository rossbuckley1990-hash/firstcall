from copy import deepcopy
from hashlib import sha256
import json

import pytest

from firstcall.agents.codex_live import AgentResult
from firstcall.journey_evidence import EvidenceSafety, capture_journey
import firstcall.resend001 as r


def command(text='node integration.js', code=0, status='completed', event_type='item.completed'):
    return {'type': event_type, 'item': {'type': 'command_execution', 'command': text,
            'exit_code': code, 'status': status, 'aggregated_output': 'output'}}


def proof(value):
    return r.digest(json.dumps({k: v for k, v in value.items() if k != 'proof_sha256'},
                               sort_keys=True, separators=(',', ':')))


def capture(tmp_path, files):
    root = tmp_path / 'workspace'
    root.mkdir(exist_ok=True)
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    out = tmp_path / 'evidence'
    result = capture_journey(root, out, AgentResult(0, '', '', 0, ()), (),
                             EvidenceSafety('fake-agent', 'fake-verifier'))
    return out, result


def test_completed_command_is_execution_evidence(resend_run):
    resend_run.events = [command()]
    receipt = resend_run.execute()
    assert receipt['candidate_execution_observed'] is True
    assert receipt['candidate_commands'][0] == {
        'command': 'node integration.js', 'exit_code': 0, 'status': 'completed',
        'output': 'output', 'source': 'codex_jsonl:item.completed',
    }


@pytest.mark.parametrize('events', [[], [command(event_type='item.started')], [{
    'type': 'item.completed', 'item': {'type': 'agent_message', 'text':
    'I ran node integration.js. FIRSTCALL_RESULT {"ok":true,"candidate_execution_observed":true}'},
}], [{'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 42}}]])
def test_prose_claim_started_or_malformed_events_do_not_prove_execution(resend_run, events):
    resend_run.events = events
    receipt = resend_run.execute()
    assert receipt['candidate_execution_observed'] is False
    assert receipt['candidate_commands'] == []


def test_commands_preserve_order_status_and_exact_text(resend_run):
    resend_run.events = [command('pwd'), command('node  integration.js\n', 1, 'failed'), command('ls')]
    receipt = resend_run.execute()
    assert [c['command'] for c in receipt['candidate_commands']] == ['pwd', 'node  integration.js\n', 'ls']
    assert [c['exit_code'] for c in receipt['candidate_commands']] == [0, 1, 0]
    assert [c['status'] for c in receipt['candidate_commands']] == ['completed', 'failed', 'completed']
    directory = resend_run.out / receipt['journey_evidence']['base_path']
    assert json.loads((directory / 'candidate-commands.json').read_text()) == receipt['candidate_commands']


def test_evidence_uses_actual_parsed_events_not_stdout_claim(resend_run):
    resend_run.events = []
    resend_run.stdout = json.dumps(command())
    assert resend_run.execute()['candidate_execution_observed'] is False


def test_manifest_deterministic_sorted_hashes_and_copies(tmp_path):
    files = {'z.bin': b'\x00\xff', 'nested/b.py': b'print(1)\n', 'a.txt': b'hello'}
    out, (_, _, _, manifest) = capture(tmp_path, files)
    assert [entry['path'] for entry in manifest] == sorted(files)
    for entry in manifest:
        data = files[entry['path']]
        assert entry['bytes'] == entry['persisted_bytes'] == len(data)
        assert entry['sha256'] == entry['persisted_sha256'] == sha256(data).hexdigest()
        assert (out / entry['persisted_path']).read_bytes() == data
    other = tmp_path / 'repeat'
    other.mkdir()
    _, (_, _, _, repeated) = capture(other, dict(reversed(list(files.items()))))
    assert repeated == manifest


def test_exclusions_include_nested_caches_bytecode_and_venvs(tmp_path):
    excluded = ['.git/config', 'nested/.cache/x', 'nested/__pycache__/x.pyc',
                'x.pyc', 'x.pyo', '.venv/code.py', 'venv/code.py',
                '.pytest_cache/x', '.mypy_cache/x', '.ruff_cache/x',
                '.tox/x', '.nox/x', 'node_modules/x', '.firstcall/metadata.json',
                'custom-env/pyvenv.cfg', 'custom-env/lib/secret.py']
    out, (_, _, _, manifest) = capture(tmp_path, {**{p: b'excluded' for p in excluded}, 'integration.py': b'safe'})
    assert [entry['path'] for entry in manifest] == ['integration.py']
    assert [p.relative_to(out / 'workspace').as_posix() for p in (out / 'workspace').rglob('*') if p.is_file()] == ['integration.py']


def test_symlinks_cannot_escape_workspace(tmp_path):
    root = tmp_path / 'workspace'
    root.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'secret').write_text('must never read')
    (root / 'escape-file').symlink_to(outside / 'secret')
    (root / 'escape-directory').symlink_to(outside, target_is_directory=True)
    (root / 'broken').symlink_to(outside / 'missing')
    (root / 'loop').symlink_to(root, target_is_directory=True)
    out, (_, _, _, manifest) = capture(tmp_path, {'safe.txt': b'safe'})
    assert [entry['path'] for entry in manifest] == ['safe.txt']
    assert b'must never read' not in b''.join(p.read_bytes() for p in out.rglob('*') if p.is_file())


@pytest.mark.parametrize('credential', ['agent_key', 'verifier_key'])
@pytest.mark.parametrize('location', ['stdout', 'stderr', 'file', 'binary', 'command', 'verification'])
def test_credentials_never_persist_in_any_evidence(resend_run, credential, location):
    secret = getattr(resend_run, credential)
    if location in {'stdout', 'stderr'}:
        setattr(resend_run, location, secret)
    elif location in {'file', 'binary'}:
        resend_run.files['integration.py'] = (b'\xff' if location == 'binary' else b'') + secret.encode()
    elif location == 'command':
        resend_run.events = [command('echo ' + secret)]
    else:
        resend_run.verification.reason = secret
    receipt = resend_run.execute()
    persisted = list(resend_run.out.rglob('*'))
    for path in persisted:
        if path.is_file():
            assert secret.encode() not in path.read_bytes()
    assert secret not in json.dumps(receipt)
    assert receipt['evidence_integrity']['status'] == 'redacted'
    assert receipt['journey_evidence']['evidence_integrity']['status'] == 'redacted'
    assert receipt['proof_sha256'] == proof(receipt)


def test_repository_patterns_apply_to_unknown_keys(tmp_path):
    fake = 're_' + 'Q2' * 20
    out, (journey, _, _, manifest) = capture(tmp_path, {'integration.py': fake.encode()})
    assert journey['evidence_integrity']['status'] == 'redacted'
    assert fake.encode() not in (out / 'workspace/integration.py').read_bytes()
    assert manifest[0]['sha256'] == sha256(fake.encode()).hexdigest()
    assert manifest[0]['persisted_sha256'] != manifest[0]['sha256']


def test_credential_filename_is_not_persisted(tmp_path):
    out, (journey, _, _, manifest) = capture(tmp_path, {'fake-agent.txt': b'safe'})
    assert manifest[0]['evidence_integrity'] == 'omitted_unsafe_path'
    assert journey['evidence_integrity']['status'] == 'redacted'
    assert not (out / 'workspace').exists()
    assert b'fake-agent' not in (out / 'workspace-manifest.json').read_bytes()


def test_json_escaped_credentials_are_redacted(tmp_path):
    secret = 'fake-"unicode-\u00e9-secret'
    safety = EvidenceSafety(secret, 'verifier-fake')
    encoded = json.dumps({'text': secret}).encode()
    safe = safety.clean(encoded, 'stdout')
    assert secret not in json.loads(safe)['text']
    assert json.loads(safe)['text'] == '[REDACTED]'


def test_receipt_binds_all_evidence_and_provenance(resend_run):
    resend_run.files['integration.py'] = b'print("candidate")\n'
    resend_run.events = [command()]
    receipt = resend_run.execute()
    assert receipt['proof_sha256'] == proof(receipt)
    for name, value in resend_run.provenance.items():
        assert receipt[name] == value
    for field in [*resend_run.provenance, 'execution_nonce', 'run_id', 'started_at',
                  'candidate_commands', 'candidate_execution_observed', 'journey_evidence',
                  'evidence_integrity']:
        modified = deepcopy(receipt)
        modified[field] = 'tampered'
        assert proof(modified) != receipt['proof_sha256']
    directory = resend_run.out / receipt['journey_evidence']['base_path']
    assert (directory / f"receipt-{receipt['proof_sha256']}.json").exists()
    for entry in receipt['journey_evidence']['files']:
        data = (directory / entry['path']).read_bytes()
        assert sha256(data).hexdigest() == entry['sha256']
    assert not resend_run.workspaces[0].exists()


def test_cohort_summary_is_content_addressed_and_history_untouched(resend_run, monkeypatch):
    from firstcall import preflight
    from types import SimpleNamespace
    resend_run.out.mkdir()
    history = {name: b'immutable historical evidence' for name in ['01-old.json', 'summary.json', 'preflight.json']}
    for name, data in history.items():
        (resend_run.out / name).write_bytes(data)
    monkeypatch.setattr(r, 'apparatus_provenance', lambda: dict(resend_run.provenance))
    monkeypatch.setattr(r, 'new_execution_nonce', lambda: 'abcdef123456')
    monkeypatch.setattr(preflight, 'run_preflight', lambda key: preflight.PreflightResult(True, True, True, True, 0, True, None))

    def version_only(argv, **kwargs):
        assert argv == ['codex', '--version']
        return SimpleNamespace(stdout='fixture-codex')

    monkeypatch.setattr(r.subprocess, 'run', version_only)
    r.main()
    for name, data in history.items():
        assert (resend_run.out / name).read_bytes() == data
    cohort = resend_run.out / 'executions/abcdef123456'
    summary_path, = cohort.glob('summary-*.json')
    summary = json.loads(summary_path.read_text())
    assert summary['proof_sha256'] == proof(summary)
    assert summary_path.name == f"summary-{proof(summary)}.json"
    assert summary['execution_nonce'] == 'abcdef123456'
    for name, value in resend_run.provenance.items():
        assert summary[name] == value
    receipts = [json.loads(path.read_text()) for path in sorted(cohort.glob('R*/receipt-*.json'))]
    assert len(receipts) == 3
    assert summary['run_proofs'] == [receipt['proof_sha256'] for receipt in receipts]
    assert len({receipt['subject'] for receipt in receipts}) == 3
    assert len(resend_run.verifier.call_args_list) == 3
    assert (cohort / 'preflight.json').exists()


def test_capture_survives_verifier_failure_before_cleanup(resend_run):
    resend_run.stdout = resend_run.agent_key
    resend_run.files['integration.py'] = b'candidate'
    resend_run.verifier.side_effect = RuntimeError('mock verification unavailable')
    with pytest.raises(RuntimeError, match='mock verification unavailable'):
        resend_run.execute()
    directory = resend_run.out / 'executions/abcdef123456/R01'
    assert (directory / 'workspace/integration.py').read_bytes() == b'candidate'
    assert (directory / 'codex.stdout.jsonl').read_text() == '[REDACTED]'
    integrity = json.loads((directory / 'evidence-integrity.json').read_text())
    assert integrity['status'] == 'redacted'
    assert not resend_run.workspaces[0].exists()


def test_available_command_fields_and_boolean_exit_code(resend_run):
    resend_run.events = [command(code=True)]
    del resend_run.events[0]['item']['status']
    receipt = resend_run.execute()
    assert receipt['candidate_execution_observed'] is True
    assert receipt['candidate_commands'][0]['exit_code'] is None
    assert receipt['candidate_commands'][0]['status'] is None
