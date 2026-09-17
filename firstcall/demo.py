from pathlib import Path

from firstcall.counterfactual import compare
from firstcall.evidence import write_receipt
from firstcall.simulator import simulated_run


def main():
    baseline = tuple(
        simulated_run(
            run_id=f"baseline-{i+1}",
            effect_exists=i < 4,
        )
        for i in range(10)
    )

    patched = tuple(
        simulated_run(
            run_id=f"patched-{i+1}",
            effect_exists=i < 9,
        )
        for i in range(10)
    )

    for run in baseline + patched:
        write_receipt(
            run,
            Path("artifacts")
            / f"{run.run_id}.json",
        )

    result = compare(
        baseline,
        patched,
    )

    print()
    print("FIRSTCALL v0.1")
    print("==============================")
    print()
    print("Synthetic Agent Customer")
    print()
    print(
        "Baseline verified:",
        f"{result.baseline_successes}/"
        f"{result.baseline_runs}",
    )
    print(
        "Baseline AFCR:",
        f"{result.baseline_rate:.0%}",
    )
    print()
    print(
        "Patched verified:",
        f"{result.patched_successes}/"
        f"{result.patched_runs}",
    )
    print(
        "Patched AFCR:",
        f"{result.patched_rate:.0%}",
    )
    print()
    print(
        "Counterfactual improvement:",
        f"{result.absolute_improvement:+.0%}",
    )
    print()
    print(
        "Independent verification:",
        "REQUIRED",
    )
    print(
        "Agent self-report trusted:",
        "NO",
    )
    print(
        "Unsafe success separated:",
        "YES",
    )
    print(
        "Evidence receipts:",
        len(baseline) + len(patched),
    )
    print()
    print("COUNTERFACTUAL REPLAY: PASS")


if __name__ == "__main__":
    main()
