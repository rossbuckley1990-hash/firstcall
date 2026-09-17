from pathlib import Path

from firstcall.repo_security import scan_repository


def test_repository_contains_no_detected_credentials():
    root = Path(__file__).resolve().parents[1]

    assert scan_repository(root) == []

def test_resend_pattern_does_not_match_identifier_substring(tmp_path):
    """
    Regression: ordinary Python identifiers containing re_ must not
    be interpreted as Resend credentials.
    """
    from firstcall.repo_security import scan_repository

    p = tmp_path / "example.py"
    p.write_text(
        "def test_completed_failure_preserves_exit_and_output():\n"
        "    pass\n"
    )

    assert scan_repository(tmp_path) == []


def test_resend_pattern_still_detects_key_shaped_secret(tmp_path):
    """
    Hardening control: fixing the identifier false positive must not
    disable detection of actual Resend-key-shaped values.
    """
    from firstcall.repo_security import scan_repository

    p = tmp_path / "leak.txt"

    # Construct the fixture so the repository scanner does not flag
    # this test source itself merely for containing the test secret.
    fake = "re_" + ("A1b2C3d4E5f6G7h8J9k0" * 2)

    p.write_text(fake)

    assert scan_repository(tmp_path)
