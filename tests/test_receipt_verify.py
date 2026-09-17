import json

from firstcall.receipt_verify import proof_sha256, verify_receipt


def test_receipt_self_verifies(tmp_path):
    receipt = {
        "experiment": "TEST",
        "verdict": "PROVEN_SUCCESS",
        "value": 42,
    }
    receipt["proof_sha256"] = proof_sha256(receipt)

    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(receipt))

    ok, recorded, calculated = verify_receipt(p)

    assert ok is True
    assert recorded == calculated


def test_receipt_tampering_is_detected(tmp_path):
    receipt = {
        "experiment": "TEST",
        "verdict": "PROVEN_SUCCESS",
        "value": 42,
    }
    receipt["proof_sha256"] = proof_sha256(receipt)

    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(receipt))

    tampered = json.loads(p.read_text())
    tampered["value"] = 43
    p.write_text(json.dumps(tampered))

    ok, _, _ = verify_receipt(p)

    assert ok is False
