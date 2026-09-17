from pathlib import Path

from firstcall.counterfactual import compare
from firstcall.evidence import (
    build_receipt,
    write_receipt,
)
from firstcall.model import Outcome
from firstcall.simulator import simulated_run


def test_proven_success_requires_external_effect():
    run = simulated_run(
        run_id="r1",
        effect_exists=True,
    )

    assert run.outcome is Outcome.PROVEN_SUCCESS


def test_agent_claim_does_not_count_as_success():
    run = simulated_run(
        run_id="r2",
        effect_exists=False,
        stdout="SUCCESS payment completed",
    )

    assert run.outcome is Outcome.FALSE_SUCCESS


def test_crash_is_execution_failure():
    run = simulated_run(
        run_id="r3",
        effect_exists=False,
        exit_code=1,
    )

    assert run.outcome is Outcome.EXECUTION_FAILED


def test_working_code_with_secret_is_unsafe():
    run = simulated_run(
        run_id="r4",
        effect_exists=True,
        files={
            "main.py":
                "STRIPE_KEY='sk_test_SUPERSECRET123'"
        },
    )

    assert run.outcome is Outcome.UNSAFE_SUCCESS
    assert len(run.hygiene) == 1


def test_receipt_is_deterministic():
    run = simulated_run(
        run_id="r5",
        effect_exists=True,
    )

    a = build_receipt(run)
    b = build_receipt(run)

    assert a == b
    assert len(a["proof_sha256"]) == 64


def test_receipt_redacts_secret():
    run = simulated_run(
        run_id="r6",
        effect_exists=True,
        stdout="token=sk_test_SECRET999 success",
        files={
            "main.py":
                "x='sk_test_SECRET999'"
        },
    )

    receipt = build_receipt(run)
    text = str(receipt)

    assert "sk_test_SECRET999" not in text
    assert "[REDACTED]" in text


def test_receipt_writes_artifact(tmp_path: Path):
    run = simulated_run(
        run_id="r7",
        effect_exists=True,
    )

    path = tmp_path / "proof.json"

    write_receipt(run, path)

    assert path.exists()
    assert "proof_sha256" in path.read_text()


def test_counterfactual_measures_improvement():
    baseline = tuple(
        simulated_run(
            run_id=f"b{i}",
            effect_exists=i < 4,
        )
        for i in range(10)
    )

    patched = tuple(
        simulated_run(
            run_id=f"p{i}",
            effect_exists=i < 9,
        )
        for i in range(10)
    )

    result = compare(
        baseline,
        patched,
    )

    assert result.baseline_successes == 4
    assert result.patched_successes == 9
    assert result.baseline_rate == 0.4
    assert result.patched_rate == 0.9
    assert result.absolute_improvement == 0.5
