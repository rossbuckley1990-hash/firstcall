import json
from types import SimpleNamespace

import firstcall.postmark_preflight as p


def completed(payload, returncode=0):
    return SimpleNamespace(
        returncode=returncode,
        stdout=json.dumps(payload),
        stderr="",
    )


def test_accepts_sandbox_server(monkeypatch):
    monkeypatch.setattr(
        p.subprocess,
        "run",
        lambda *args, **kwargs: completed(
            {
                "ID": 123,
                "DeliveryType": "Sandbox",
            }
        ),
    )

    result = p.inspect_server("fake-token")

    assert result.safe is True
    assert result.delivery_type == "Sandbox"
    assert result.server_id == 123


def test_rejects_live_server(monkeypatch):
    monkeypatch.setattr(
        p.subprocess,
        "run",
        lambda *args, **kwargs: completed(
            {
                "ID": 456,
                "DeliveryType": "Live",
            }
        ),
    )

    result = p.inspect_server("fake-token")

    assert result.safe is False
    assert result.delivery_type == "Live"
    assert "not Sandbox" in result.reason


def test_rejects_missing_delivery_type(monkeypatch):
    monkeypatch.setattr(
        p.subprocess,
        "run",
        lambda *args, **kwargs: completed(
            {"ID": 789}
        ),
    )

    assert p.inspect_server(
        "fake-token"
    ).safe is False


def test_rejects_api_failure(monkeypatch):
    monkeypatch.setattr(
        p.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=22,
            stdout="",
            stderr="failure",
        ),
    )

    assert p.inspect_server(
        "fake-token"
    ).safe is False


def test_rejects_missing_token():
    assert p.inspect_server("").safe is False
