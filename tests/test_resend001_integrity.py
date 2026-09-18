from hashlib import sha256
from pathlib import Path
import re

import pytest

import firstcall.resend001 as r


def test_credential_fingerprint_is_12_lower_hex():
    secret = "re_test_customer_credential"

    fp = r.credential_fingerprint(secret)

    assert fp == sha256(
        secret.encode()
    ).hexdigest()[:12]

    assert re.fullmatch(
        r"[0-9a-f]{12}",
        fp,
    )

    assert secret not in fp


def test_credential_fingerprint_is_deterministic():
    value = "same-secret-value"

    assert (
        r.credential_fingerprint(value)
        == r.credential_fingerprint(value)
    )


def test_different_credentials_have_separate_fingerprints():
    result = r.credential_provenance(
        "agent-secret-A",
        "verifier-secret-B",
    )

    assert result["credential_separation"] is True

    assert (
        result["agent_credential_fingerprint"]
        != result["verifier_credential_fingerprint"]
    )


def test_equal_credentials_fail_closed():
    with pytest.raises(
        RuntimeError,
        match="credentials must differ",
    ):
        r.credential_provenance(
            "same-secret",
            "same-secret",
        )


def test_missing_agent_credential_fails_closed():
    with pytest.raises(
        RuntimeError,
        match="RESEND_API_KEY",
    ):
        r.credential_provenance(
            "",
            "verifier-secret",
        )


def test_missing_verifier_credential_fails_closed():
    with pytest.raises(
        RuntimeError,
        match="FIRSTCALL_RESEND_VERIFIER_KEY",
    ):
        r.credential_provenance(
            "agent-secret",
            "",
        )


def test_file_sha256_matches_content(tmp_path):
    target = tmp_path / "fixture.txt"
    target.write_bytes(b"FIRSTCALL")

    expected = sha256(
        b"FIRSTCALL"
    ).hexdigest()

    assert r.file_sha256(target) == expected


def test_apparatus_provenance_has_required_fields(
    monkeypatch,
):
    monkeypatch.setattr(
        r,
        "git_output",
        lambda *args: "a" * 40,
    )

    monkeypatch.setattr(
        r,
        "tracked_repo_dirty",
        lambda: False,
    )

    result = r.apparatus_provenance()

    assert result["apparatus_commit"] == "a" * 40
    assert result["apparatus_dirty"] is False

    for key in (
        "docs_sha256",
        "task_sha256",
        "policy_sha256",
    ):
        value = result[key]

        assert isinstance(value, str)
        assert re.fullmatch(
            r"[0-9a-f]{64}",
            value,
        )


def test_tracked_dirty_state_ignores_untracked_files(
    tmp_path,
):
    # Structural contract:
    # implementation uses git diff rather than git status,
    # therefore ordinary untracked files are not apparatus dirtiness.
    source = Path(
        r.__file__
    ).read_text()

    start = source.index(
        "def tracked_repo_dirty"
    )

    end = source.index(
        "\ndef apparatus_provenance",
        start,
    )

    body = source[start:end]

    assert '"diff"' in body
    assert '"--cached"' in body
    assert "status" not in body


def test_provenance_contains_no_full_credentials():
    agent = "agent-super-secret-value"
    verifier = "verifier-super-secret-value"

    result = r.credential_provenance(
        agent,
        verifier,
    )

    serialised = repr(result)

    assert agent not in serialised
    assert verifier not in serialised


def test_phase1_subject_identity_remains_intact():
    nonce = "abcdef123456"

    assert r.build_run_subject(
        nonce,
        "R01",
    ) == (
        "FIRSTCALL RESEND-001 "
        "abcdef123456 R01"
    )
