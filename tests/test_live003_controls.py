from pathlib import Path


def test_live003_never_executes_candidate():
    root = Path(__file__).resolve().parents[1]

    source = (
        root / "firstcall" / "live003.py"
    ).read_text()

    assert '"firstcall_executes_candidate": False' in source
    assert '"executed_by_firstcall": False' in source


def test_live003_has_ten_fresh_runs():
    from firstcall.live003 import RUNS

    assert RUNS == 10
