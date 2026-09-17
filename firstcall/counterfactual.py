from __future__ import annotations

from dataclasses import dataclass

from firstcall.model import Outcome, RunResult


@dataclass(frozen=True)
class CounterfactualResult:
    baseline_runs: int
    patched_runs: int
    baseline_successes: int
    patched_successes: int
    baseline_rate: float
    patched_rate: float
    absolute_improvement: float


def proven(
    run: RunResult,
) -> bool:
    return run.outcome is Outcome.PROVEN_SUCCESS


def compare(
    baseline: tuple[RunResult, ...],
    patched: tuple[RunResult, ...],
) -> CounterfactualResult:
    if not baseline or not patched:
        raise ValueError(
            "Both experiment arms require runs"
        )

    b = sum(proven(run) for run in baseline)
    p = sum(proven(run) for run in patched)

    br = b / len(baseline)
    pr = p / len(patched)

    return CounterfactualResult(
        baseline_runs=len(baseline),
        patched_runs=len(patched),
        baseline_successes=b,
        patched_successes=p,
        baseline_rate=br,
        patched_rate=pr,
        absolute_improvement=pr - br,
    )
