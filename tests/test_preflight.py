from firstcall.preflight import PreflightResult


def test_invalid_preflight_is_explicit():
    result = PreflightResult(
        credential_present=True,
        workspace_writable=True,
        agent_target_reachable=False,
        verifier_reachable=True,
        agent_exit_code=0,
        valid=False,
        reason="TARGET_NETWORK_UNAVAILABLE",
    )

    assert result.valid is False
    assert result.reason == "TARGET_NETWORK_UNAVAILABLE"


def test_valid_preflight_requires_all_controls():
    result = PreflightResult(
        credential_present=True,
        workspace_writable=True,
        agent_target_reachable=True,
        verifier_reachable=True,
        agent_exit_code=0,
        valid=True,
        reason=None,
    )

    assert result.valid is True
