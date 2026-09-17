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


def test_rejects_matching_email_created_before_run(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST nonce123 R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    monkeypatch.setattr(
        verifier,
        "_list",
        lambda *, after=None: {
            "data": [
                {
                    "id": "historical-email",
                    "subject": "FIRSTCALL TEST nonce123 R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T20:59:59+00:00",
                    "last_event": "delivered",
                }
            ]
        },
    )

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert result.observed is False
    assert result.email_id is None


def test_selects_new_effect_not_historical_match(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST nonce456 R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    monkeypatch.setattr(
        verifier,
        "_list",
        lambda *, after=None: {
            "data": [
                {
                    "id": "historical-email",
                    "subject": "FIRSTCALL TEST nonce456 R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T20:00:00+00:00",
                    "last_event": "delivered",
                },
                {
                    "id": "current-email",
                    "subject": "FIRSTCALL TEST nonce456 R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:01+00:00",
                    "last_event": "delivered",
                },
            ]
        },
    )

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert result.observed is True
    assert result.email_id == "current-email"


def test_rejects_duplicate_current_effects(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST nonce789 R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    monkeypatch.setattr(
        verifier,
        "_list",
        lambda *, after=None: {
            "data": [
                {
                    "id": "current-email-1",
                    "subject": "FIRSTCALL TEST nonce789 R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:01+00:00",
                    "last_event": "delivered",
                },
                {
                    "id": "current-email-2",
                    "subject": "FIRSTCALL TEST nonce789 R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:02+00:00",
                    "last_event": "delivered",
                },
            ]
        },
    )

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert result.observed is False
    assert result.email_id is None
    assert result.reason == "multiple matching vendor-side emails observed"


def test_rejects_duplicate_effect_hidden_on_second_page(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST paginated R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    pages = [
        {
            "object": "list",
            "has_more": True,
            "data": [
                {
                    "id": "current-email-1",
                    "subject": "FIRSTCALL TEST paginated R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:03+00:00",
                    "last_event": "delivered",
                },
                {
                    "id": "unrelated-email-A",
                    "subject": "something else",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:02+00:00",
                    "last_event": "delivered",
                },
                {
                    "id": "unrelated-email-B",
                    "subject": "another subject",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:01+00:00",
                    "last_event": "delivered",
                }
            ],
        },
        {
            "object": "list",
            "has_more": False,
            "data": [
                {
                    "id": "current-email-2",
                    "subject": "FIRSTCALL TEST paginated R01",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:02+00:00",
                    "last_event": "delivered",
                }
            ],
        },
    ]

    calls = []

    def fake_list(*, after=None):
        calls.append(after)
        return pages[len(calls) - 1]

    monkeypatch.setattr(verifier, "_list", fake_list)

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert calls == [None, "unrelated-email-B"]
    assert result.observed is False
    assert result.email_id is None
    assert result.reason == "multiple matching vendor-side emails observed"


def test_fails_closed_on_repeated_pagination_cursor(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST loop R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    calls = []

    def fake_list(*, after=None):
        calls.append(after)
        return {
            "object": "list",
            "has_more": True,
            "data": [
                {
                    "id": "repeated-cursor",
                    "subject": "irrelevant",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:01+00:00",
                    "last_event": "delivered",
                }
            ],
        }

    monkeypatch.setattr(verifier, "_list", fake_list)

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert calls == [None, "repeated-cursor"]
    assert result.observed is False
    assert result.email_id is None
    assert result.reason == "invalid verifier pagination cursor"


def test_fails_closed_on_repeated_pagination_cursor(monkeypatch):
    from firstcall.verifiers.resend import ResendVerifier

    verifier = ResendVerifier(
        api_key="verifier-key",
        subject="FIRSTCALL TEST loop R01",
        recipient="delivered@resend.dev",
        created_after="2026-09-17T21:00:00+00:00",
    )

    calls = []

    def fake_list(*, after=None):
        calls.append(after)
        return {
            "object": "list",
            "has_more": True,
            "data": [
                {
                    "id": "repeated-cursor",
                    "subject": "irrelevant",
                    "to": ["delivered@resend.dev"],
                    "created_at": "2026-09-17T21:00:01+00:00",
                    "last_event": "delivered",
                }
            ],
        }

    monkeypatch.setattr(verifier, "_list", fake_list)

    result = verifier.verify(
        attempts=1,
        delay=0,
    )

    assert calls == [None, "repeated-cursor"]
    assert result.observed is False
    assert result.email_id is None
    assert result.reason == "invalid verifier pagination cursor"
