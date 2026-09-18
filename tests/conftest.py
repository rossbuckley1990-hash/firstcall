"""Offline RESEND-001 runtime fixture; no customer process or network."""
from dataclasses import dataclass
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from firstcall.agents.codex_live import AgentResult
import firstcall.resend001 as r


@pytest.fixture
def resend_run(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('real process/network forbidden in runtime test')

    monkeypatch.setattr('subprocess.run', forbidden)
    monkeypatch.setattr('subprocess.Popen', forbidden)
    monkeypatch.setattr('socket.socket', forbidden)
    monkeypatch.setattr('urllib.request.urlopen', forbidden)
    exp = tmp_path / 'experiment'
    exp.mkdir()
    for name, content in [('docs.md', 'fixture docs\n'), ('task.txt', 'task {RUN_ID}'),
                          ('policy.json', '{}')]:
        (exp / name).write_text(content)
    monkeypatch.setattr(r, 'EXP', exp)
    monkeypatch.setattr(r, 'OUT', tmp_path / 'artifacts')
    agent_key, verifier_key = 'fake-agent-credential', 'fake-verifier-credential'
    monkeypatch.setenv('RESEND_API_KEY', agent_key)
    monkeypatch.setenv('FIRSTCALL_RESEND_VERIFIER_KEY', verifier_key)
    provenance = {
        'apparatus_commit': 'a' * 40, 'apparatus_dirty': True,
        **{name + '_sha256': r.file_sha256(exp / file)
           for name, file in [('docs', 'docs.md'), ('task', 'task.txt'), ('policy', 'policy.json')]},
        **r.credential_provenance(agent_key, verifier_key),
    }
    timeline = []
    stamp = '2031-02-03T04:05:06.123456+00:00'

    def now():
        timeline.append('utc_now')
        return stamp

    monkeypatch.setattr(r, 'utc_now', Mock(side_effect=now))
    state = SimpleNamespace(events=(), stdout=None, stderr='', files={}, workspaces=[],
                            timeline=timeline, stamp=stamp, provenance=provenance,
                            agent_key=agent_key, verifier_key=verifier_key)

    @dataclass
    class Workspace:
        path: object

        def cleanup(self):
            import shutil
            timeline.append('cleanup')
            # Evidence must exist before any temporary bytes are removed.
            assert list(r.OUT.rglob('workspace-manifest.json'))
            shutil.rmtree(self.path)

    def create():
        path = tmp_path / f'workspace-{len(state.workspaces)}'
        path.mkdir()
        state.workspaces.append(path)
        return Workspace(path)

    monkeypatch.setattr(r, 'create_workspace', create)

    def run(**kwargs):
        timeline.append('customer_execution')
        for name, data in state.files.items():
            path = kwargs['cwd'] / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        stdout = state.stdout
        if stdout is None:
            stdout = '\n'.join(json.dumps(event) for event in state.events)
        return AgentResult(0, stdout, state.stderr, 12, tuple(state.events))

    state.runner = Mock()
    state.runner.run.side_effect = run
    monkeypatch.setattr(r, 'CodexLiveRunner', Mock(return_value=state.runner))
    state.verification = SimpleNamespace(observed=False, email_id=None, last_event=None, reason=None)

    def verify_factory(**kwargs):
        timeline.append('verifier_constructed')
        return SimpleNamespace(verify=lambda: state.verification)

    state.verifier = Mock(side_effect=verify_factory)
    monkeypatch.setattr(r, 'ResendVerifier', state.verifier)

    def execute(number=1, nonce='abcdef123456'):
        return r.run_one(provenance=provenance, execution_nonce=nonce, number=number,
                         key=agent_key, version='fixture-codex')

    state.execute = execute
    state.out = r.OUT
    return state


@pytest.fixture(autouse=True)
def postmark_wait_is_mocked(monkeypatch):
    # Retry scheduling is asserted with an injected recorder in verifier tests.
    # Mock-only cohort tests must never spend wall time waiting for a vendor.
    monkeypatch.setattr('firstcall.verifiers.postmark.time', SimpleNamespace(sleep=Mock()))
