from pathlib import Path

from firstcall.repo_security import scan_repository


def test_repository_contains_no_detected_credentials():
    root = Path(__file__).resolve().parents[1]

    assert scan_repository(root) == []
