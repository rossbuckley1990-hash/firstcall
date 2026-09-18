import re

import firstcall.resend001 as r


def test_execution_nonce_shape_and_freshness():
    a = r.new_execution_nonce()
    b = r.new_execution_nonce()

    assert re.fullmatch(r"[0-9a-f]{12}", a)
    assert re.fullmatch(r"[0-9a-f]{12}", b)
    assert a != b


def test_cohort_subjects_share_nonce_and_differ_by_run():
    nonce = "a1b2c3d4e5f6"

    subjects = [
        r.build_run_subject(nonce, run_id)
        for run_id in ("R01", "R02", "R03")
    ]

    assert subjects == [
        "FIRSTCALL RESEND-001 a1b2c3d4e5f6 R01",
        "FIRSTCALL RESEND-001 a1b2c3d4e5f6 R02",
        "FIRSTCALL RESEND-001 a1b2c3d4e5f6 R03",
    ]

    assert len(set(subjects)) == 3


def test_utc_now_is_timezone_aware_utc():
    value = r.utc_now()

    assert "+00:00" in value or value.endswith("Z")


def test_runner_wires_created_after_to_started_at():
    from pathlib import Path

    source = Path(
        r.__file__
    ).read_text()

    assert "started_at = utc_now()" in source
    assert "created_after=started_at" in source
    assert '"started_at": started_at' in source


def test_runtime_exact_timestamp_is_bound_to_verifier(resend_run):
    receipt = resend_run.execute()

    r.utc_now.assert_called_once_with()
    assert resend_run.timeline == [
        'utc_now', 'customer_execution', 'verifier_constructed', 'cleanup',
    ]
    resend_run.runner.run.assert_called_once()
    assert resend_run.verifier.call_args.kwargs['created_after'] == resend_run.stamp
    assert receipt['started_at'] == resend_run.stamp
    assert receipt['subject'] == resend_run.verifier.call_args.kwargs['subject']
    assert not resend_run.workspaces[0].exists()
