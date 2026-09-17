from pathlib import Path

def test_runner_hardening_is_present():
    source = Path("firstcall/cf001_baseline.py").read_text()
    checks = [
        '["git", "init", "-q"]',
        "thread.started",
        "turn.started",
        "agent_launch_failed",
        'verdict = "UNKNOWN"',
        "codex.stdout.jsonl",
        "codex.stderr.txt",
        "shutil.copytree",
    ]
    for check in checks:
        assert check in source


def test_verifier_unavailable_maps_to_unknown():
    source = Path("firstcall/cf001_baseline.py").read_text()
    assert 'verification.get("observed") is None' in source
    assert 'invalid_reason = "verifier_unavailable"' in source
