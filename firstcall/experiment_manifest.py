from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(
    *,
    experiment: str,
    docs_path: Path,
    task_path: Path,
    runs: int,
    provider: str,
    verifier: str,
) -> dict:
    return {
        "schema": "firstcall.experiment-manifest.v1",
        "experiment": experiment,
        "runs": runs,
        "provider": provider,
        "verifier": verifier,
        "docs_sha256": sha256_file(docs_path),
        "task_sha256": sha256_file(task_path),
        "controls": {
            "fresh_workspace": True,
            "firstcall_executes_candidate": False,
            "independent_vendor_check": True,
            "structured_claim_required": True,
        },
    }


def manifest_sha256(manifest: dict) -> str:
    payload = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()
