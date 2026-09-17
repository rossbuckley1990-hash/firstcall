from firstcall.verifiers.resend import (
    ResendObservation,
)


def test_resend_observation_is_explicit():
    result = ResendObservation(
        observed=True,
        email_id="email_123",
        subject="FIRSTCALL",
        recipient="delivered@resend.dev",
        last_event="delivered",
        reason=None,
    )

    assert result.observed is True
    assert result.email_id == "email_123"
