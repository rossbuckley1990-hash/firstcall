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


# New measurement semantics: every observation and wait is deterministic/offline.
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from firstcall.grade import grade
from firstcall.model import Execution, Outcome, Verification

MESSAGE_ID = '74fdbaad-6b97-4d24-b16f-6d3e2b6990e6'
OTHER_ID = 'd2367896-2347-4a2b-abb6-2cfe328ed777'


@pytest.fixture(autouse=True)
def no_live_verifier_io(monkeypatch):
    blocked = Mock(side_effect=AssertionError('real network/process forbidden'))
    monkeypatch.setattr('subprocess.run', blocked)
    monkeypatch.setattr('subprocess.Popen', blocked)
    monkeypatch.setattr('socket.socket', blocked)
    yield
    blocked.assert_not_called()


def message(**changes):
    return dict({
        'MessageID': MESSAGE_ID, 'Subject': SUBJECT,
        'Recipients': [RECIPIENT], 'ReceivedAt': BOUNDARY,
        'Sandboxed': True, 'Status': 'Sent',
    }, **changes)


def sequence(monkeypatch, observations, **options):
    timeline = []
    v = PostmarkVerifier(
        server_token='verifier-secret', subject=SUBJECT, recipient=RECIPIENT,
        created_after=BOUNDARY, wait=lambda seconds: timeline.append(('wait', seconds)),
        **options,
    )
    replies = iter(observations)

    def observe():
        timeline.append('observe')
        result = next(replies)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(v, '_list', observe)
    return v, timeline


def test_visible_first_observation_needs_no_wait(monkeypatch):
    v, timeline = sequence(monkeypatch, [{'Messages': [message()]}],
                           expected_message_id=MESSAGE_ID.upper())
    result = v.verify()
    assert result.observed and result.message_id == MESSAGE_ID
    assert timeline == ['observe']


@pytest.mark.parametrize('first', [
    {'Messages': []}, RuntimeError('Postmark verification request failed'),
    OSError('verifier-secret'), subprocess.TimeoutExpired(['curl', 'verifier-secret'], 10),
])
def test_absent_or_transport_error_then_visible(monkeypatch, first):
    v, timeline = sequence(monkeypatch, [first, {'Messages': [message()]}],
                           expected_message_id=MESSAGE_ID)
    assert v.verify().observed is True
    assert timeline == ['observe', ('wait', 5.0), 'observe']


def test_visible_on_last_bounded_observation(monkeypatch):
    v, timeline = sequence(monkeypatch, [
        {'Messages': []}, {'Messages': []}, {'Messages': [message()]},
    ], expected_message_id=MESSAGE_ID)
    assert v.verify().observed
    assert timeline == ['observe', ('wait', 5.0), 'observe', ('wait', 5.0), 'observe']


@pytest.mark.parametrize('candidate_id', [None, MESSAGE_ID])
def test_entire_window_absent_candidate_claim_is_not_proof(monkeypatch, candidate_id):
    v, timeline = sequence(monkeypatch, [{'Messages': []}] * 3,
                           expected_message_id=candidate_id)
    result = v.verify()
    assert not result.observed and result.message_id is None
    assert result.reason == 'vendor effect not observed'
    assert timeline == ['observe', ('wait', 5.0), 'observe', ('wait', 5.0), 'observe']
    assert grade(Execution(0, 'success', '', {}), Verification(result.observed, {}), ()) != Outcome.PROVEN_SUCCESS


@pytest.mark.parametrize('payload', [
    None, [], {}, {'Messages': 'invalid'}, {'Messages': [None]},
    {'Messages': [message(), None]},
    {'Messages': [message(ReceivedAt='invalid')]},
    {'Messages': [message(ReceivedAt='2026-09-18T07:00:00')]},
    {'Messages': [message(ReceivedAt=None)]},
    {'Messages': [message(Recipients=42)]},
    {'Messages': [message(Recipients=42, To=RECIPIENT)]},
    {'Messages': [message(MessageID=None)]},
    {'Messages': [message()], 'TotalCount': 2},
    {'Messages': [message()], 'TotalCount': '1'},
    {'Messages': [message()], 'TotalCount': True},
])
def test_malformed_or_incomplete_evidence_is_terminal(monkeypatch, payload):
    v, timeline = sequence(monkeypatch, [payload, {'Messages': [message()]}])
    result = v.verify()
    assert not result.observed and 'malformed' in result.reason
    assert timeline == ['observe']


@pytest.mark.parametrize('changes', [
    {'MessageID': OTHER_ID},
    {'Subject': 'wrong subject'},
    {'Recipients': ['other@example.invalid']},
    {'Sandboxed': False},
    {'Sandboxed': 'true'},
    {'Sandboxed': None},
    {'ReceivedAt': '2026-09-18T06:59:59+00:00'},
])
def test_id_does_not_override_other_correlation_or_safety(monkeypatch, changes):
    v, _ = sequence(monkeypatch, [{'Messages': [message(**changes)]}] * 3,
                    expected_message_id=MESSAGE_ID)
    assert not v.verify().observed


def test_wrong_candidate_id_for_right_subject_and_recipient(monkeypatch):
    v, timeline = sequence(monkeypatch, [{'Messages': [message()]}],
                           expected_message_id=OTHER_ID)
    result = v.verify()
    assert not result.observed and result.reason == 'vendor-side MessageID mismatch'
    assert timeline == ['observe']


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('second', [
    message(MessageID=OTHER_ID), message(),
    message(MessageID=OTHER_ID, Sandboxed=False),
])
def test_candidate_id_cannot_hide_duplicate_or_live_effect(monkeypatch, reverse, second):
    messages = [message(), second]
    if reverse:
        messages.reverse()
    v, timeline = sequence(monkeypatch, [{'Messages': messages}], expected_message_id=MESSAGE_ID)
    result = v.verify()
    assert not result.observed
    assert 'multiple' in result.reason or 'not sandboxed' in result.reason
    assert timeline == ['observe']


@pytest.mark.parametrize('value', ['', 'claimed-id', 'a' * 36, '{' + MESSAGE_ID + '}', 42])
def test_invalid_candidate_id_is_rejected_before_observation(value):
    with pytest.raises(ValueError, match='canonical UUID'):
        PostmarkVerifier(server_token='verifier-secret', subject=SUBJECT,
                         recipient=RECIPIENT, created_after=BOUNDARY, expected_message_id=value)


@pytest.mark.parametrize('options', [
    {'attempts': 0}, {'attempts': -1}, {'attempts': True}, {'attempts': 1.5},
    {'retry_delay': 0}, {'retry_delay': -1}, {'retry_delay': float('inf')},
    {'retry_delay': float('nan')},
])
def test_invalid_window_is_rejected(options):
    with pytest.raises(ValueError):
        PostmarkVerifier(server_token='verifier-secret', subject=SUBJECT,
                         recipient=RECIPIENT, created_after=BOUNDARY, **options)


def test_custom_window_and_all_transport_failures_are_bounded_and_sanitized(monkeypatch):
    v, timeline = sequence(monkeypatch, [RuntimeError('verifier-secret')] * 2,
                           attempts=2, retry_delay=1.25)
    result = v.verify()
    assert not result.observed
    assert result.reason == 'Postmark verification request failed'
    assert 'verifier-secret' not in repr(result)
    assert timeline == ['observe', ('wait', 1.25), 'observe']


@pytest.mark.parametrize('stdout,returncode,reason', [
    ('not JSON verifier-secret', 0, 'invalid JSON'),
    ('[]', 0, 'malformed response'),
    ('verifier-secret', 22, 'request failed'),
])
def test_real_list_parser_fails_closed_without_network(monkeypatch, stdout, returncode, reason):
    process = Mock(return_value=SimpleNamespace(stdout=stdout, returncode=returncode))
    monkeypatch.setattr('subprocess.run', process)
    v = verifier()
    result = v.verify()
    assert not result.observed and reason in result.reason
    assert 'verifier-secret' not in repr(result)
    process.assert_called_once()


def test_list_keeps_read_only_endpoint_and_enforces_timeout(monkeypatch):
    process = Mock(return_value=SimpleNamespace(
        stdout=json.dumps({'Messages': [message()], 'TotalCount': 1}), returncode=0,
    ))
    monkeypatch.setattr('subprocess.run', process)
    assert verifier().verify().observed
    args, kwargs = process.call_args
    assert args[0] == [
        'curl', '-sS', '--fail-with-body', '--max-time', '10', '-H',
        'X-Postmark-Server-Token: verifier-secret',
        'https://api.postmarkapp.com/messages/outbound?count=100&offset=0',
    ]
    assert kwargs == {'capture_output': True, 'text': True, 'check': False, 'timeout': 10}


def test_earlier_transport_error_is_not_relabelled_as_proven_absence(monkeypatch):
    v, _ = sequence(monkeypatch, [RuntimeError('transport'), {'Messages': []}, {'Messages': []}])
    result = v.verify()
    assert not result.observed and result.reason == 'Postmark verification request failed'


def test_legacy_to_sent_at_fallback_preserves_boundary(monkeypatch):
    item = message(To=RECIPIENT, SentAt=BOUNDARY)
    del item['Recipients']
    del item['ReceivedAt']
    v, _ = sequence(monkeypatch, [{'Messages': [item]}], expected_message_id=MESSAGE_ID)
    assert v.verify().observed


def test_full_page_without_total_cannot_establish_cardinality(monkeypatch):
    rows = [message()] + [message(Subject='unrelated')] * 99
    v, _ = sequence(monkeypatch, [{'Messages': rows}], expected_message_id=MESSAGE_ID)
    assert not v.verify().observed
