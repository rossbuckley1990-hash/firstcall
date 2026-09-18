from firstcall.verifiers.postmark import (
    PostmarkVerifier,
)


BOUNDARY = "2026-09-18T07:00:00+00:00"
SUBJECT = "FIRSTCALL MULTI-001 POSTMARK abc R01"
RECIPIENT = "test@blackhole.postmarkapp.com"


def verifier():
    return PostmarkVerifier(
        server_token="verifier-secret",
        subject=SUBJECT,
        recipient=RECIPIENT,
        created_after=BOUNDARY,
        attempts=1,
    )


def test_accepts_exactly_one_current_effect(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-current",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:00:01+00:00",
                    "Status": "Sent",
                    "Sandboxed": True,
                }
            ]
        },
    )

    result = v.verify()

    assert result.observed is True
    assert result.message_id == "pm-current"


def test_rejects_historical_matching_effect(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-old",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T06:59:59+00:00",
                    "Sandboxed": True,
                }
            ]
        },
    )

    result = v.verify()

    assert result.observed is False


def test_selects_current_not_historical(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-old",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T06:00:00+00:00",
                    "Sandboxed": True,
                },
                {
                    "MessageID": "pm-new",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:01:00+00:00",
                    "Sandboxed": True,
                },
            ]
        },
    )

    result = v.verify()

    assert result.observed is True
    assert result.message_id == "pm-new"


def test_rejects_duplicate_current_effects(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-one",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:01:00+00:00",
                    "Sandboxed": True,
                },
                {
                    "MessageID": "pm-two",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:02:00+00:00",
                    "Sandboxed": True,
                },
            ]
        },
    )

    result = v.verify()

    assert result.observed is False
    assert (
        result.reason
        == "multiple matching vendor-side messages observed"
    )


def test_rejects_wrong_recipient(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-wrong",
                    "Subject": SUBJECT,
                    "Recipients": [
                        "someone@example.com",
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:01:00+00:00",
                    "Sandboxed": True,
                }
            ]
        },
    )

    assert v.verify().observed is False


def test_rejects_wrong_subject(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-wrong",
                    "Subject": "something else",
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:01:00+00:00",
                    "Sandboxed": True,
                }
            ]
        },
    )

    assert v.verify().observed is False


def test_malformed_vendor_response_fails_closed(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": "not-a-list"
        },
    )

    result = v.verify()

    assert result.observed is False
    assert "malformed" in result.reason


def test_rejects_matching_live_effect(
    monkeypatch,
):
    v = verifier()

    monkeypatch.setattr(
        v,
        "_list",
        lambda: {
            "Messages": [
                {
                    "MessageID": "pm-live",
                    "Subject": SUBJECT,
                    "Recipients": [
                        RECIPIENT,
                    ],
                    "ReceivedAt":
                        "2026-09-18T07:03:00+00:00",
                    "Status": "Sent",
                    "Sandboxed": False,
                }
            ]
        },
    )

    result = v.verify()

    assert result.observed is False
    assert result.message_id == "pm-live"
    assert result.reason == (
        "matching vendor-side message "
        "was not sandboxed"
    )
