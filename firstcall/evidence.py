from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from firstcall.hashutil import digest
from firstcall.model import RunResult
from firstcall.redact import redact


def build_receipt(
    result: RunResult,
) -> dict:
    payload = asdict(result)

    payload["execution"]["stdout"] = redact(
        payload["execution"]["stdout"]
    )
    payload["execution"]["stderr"] = redact(
        payload["execution"]["stderr"]
    )

    payload["execution"]["generated_files"] = {
        path: redact(content)
        for path, content
        in payload["execution"]["generated_files"].items()
    }

    receipt = {
        "schema": "firstcall.run-proof.v1",
        "run": payload,
    }

    receipt["proof_sha256"] = digest(receipt)

    return receipt


def write_receipt(
    result: RunResult,
    path: Path,
) -> dict:
    receipt = build_receipt(result)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            receipt,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    return receipt
