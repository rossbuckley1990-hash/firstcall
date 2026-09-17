from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from firstcall.experiment_manifest import (
    build_manifest,
    manifest_sha256,
)
from firstcall.receipt_verify import (
    proof_sha256,
    verify_receipt,
)


SCHEMA = "firstcall.benchmark-receipt.v1"


def build_benchmark_receipt(
    *,
    experiment: str,
    run_number: int,
    docs_path: Path,
    task_path: Path,
    provider: str,
    verifier: str,
    agent_version: str,
    model: str | None,
    candidate_execution_observed: bool,
    candidate_exit_code: int | None,
    candidate_commands: list[dict[str, Any]],
    claim: dict[str, Any],
    verification: dict[str, Any],
    verdict: str,
    docs_unchanged: bool,
    forbidden_files: list[str],
    secret_leaked: bool,
) -> dict[str, Any]:

    manifest = build_manifest(
        experiment=experiment,
        docs_path=docs_path,
        task_path=task_path,
        runs=1,
        provider=provider,
        verifier=verifier,
    )

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "experiment": experiment,
        "run_number": run_number,

        "manifest": manifest,
        "manifest_sha256": manifest_sha256(manifest),

        "agent": {
            "version": agent_version,
            "model": model,
            "model_identity_status": (
                "observed"
                if model is not None
                else "unknown"
            ),
        },

        "execution": {
            "candidate_execution_observed":
                candidate_execution_observed,
            "candidate_exit_code":
                candidate_exit_code,
            "candidate_commands":
                candidate_commands,
        },

        "claim": claim,

        "verification": verification,

        "controls": {
            "fresh_workspace": True,
            "firstcall_executes_candidate": False,
            "independent_vendor_check": True,
            "structured_claim": True,
        },

        "integrity": {
            "docs_unchanged": docs_unchanged,
            "forbidden_files": forbidden_files,
            "secret_leaked": secret_leaked,
        },

        "verdict": verdict,
    }

    receipt["proof_sha256"] = proof_sha256(receipt)

    return receipt


def write_benchmark_receipt(
    receipt: dict[str, Any],
    output_path: Path,
) -> Path:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            receipt,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    ok, _, _ = verify_receipt(output_path)

    if not ok:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            "Receipt failed self-verification after write"
        )

    return output_path
