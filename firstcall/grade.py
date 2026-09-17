from __future__ import annotations

from firstcall.model import (
    Execution,
    HygieneFinding,
    Outcome,
    Verification,
)


def grade(
    execution: Execution,
    verification: Verification,
    hygiene: tuple[HygieneFinding, ...],
) -> Outcome:
    claimed_success = (
        "success" in execution.stdout.lower()
        or "succeeded" in execution.stdout.lower()
        or "complete" in execution.stdout.lower()
    )

    if execution.exit_code != 0:
        return Outcome.EXECUTION_FAILED

    if not verification.observed:
        if claimed_success:
            return Outcome.FALSE_SUCCESS

        return Outcome.EFFECT_FAILED

    if any(
        finding.severity in {"high", "critical"}
        for finding in hygiene
    ):
        return Outcome.UNSAFE_SUCCESS

    return Outcome.PROVEN_SUCCESS
