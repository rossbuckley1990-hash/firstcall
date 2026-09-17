from firstcall.agents.codex import CodexRunner


def test_codex_runner_is_available():
    runner = CodexRunner(timeout=1)
    assert runner.executable.endswith("codex")
