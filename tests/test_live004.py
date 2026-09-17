from firstcall.claim import parse_claim
from firstcall.stats import wilson


def test_structured_true_claim():
    claim = parse_claim(
        'FIRSTCALL_RESULT {"ok":true}'
    )

    assert claim.found is True
    assert claim.ok is True


def test_negative_text_is_not_success():
    claim = parse_claim(
        "failed to complete successfully"
    )

    assert claim.found is False
    assert claim.ok is None


def test_wilson_interval():
    low, high = wilson(
        4,
        10,
    )

    assert 0.16 < low < 0.18
    assert 0.68 < high < 0.70
