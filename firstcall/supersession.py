from __future__ import annotations

from pathlib import Path
import hashlib
import json


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)

    return h.hexdigest()


def snapshot_receipts(directory: Path) -> list[dict]:
    if not directory.exists():
        return []

    records = []

    for path in sorted(directory.glob("*.json")):
        records.append({
            "path": str(path),
            "sha256": sha256_file(path),
        })

    return records


def write_supersession() -> Path:
    out = Path("artifacts/supersession")
    out.mkdir(parents=True, exist_ok=True)

    record = {
        "type": "BENCHMARK_SUPERSESSION",
        "original_evidence_modified": False,
        "records": [
            {
                "experiment": "LIVE-003",
                "status": "SUPERSEDED",
                "benchmark_usable": False,
                "reason": "HARNESS_NETWORK_DISABLED",
                "detail": (
                    "Codex workspace-write sandbox prevented "
                    "target network access. A controlled A/B "
                    "test subsequently demonstrated "
                    "KEY_PRESENT=yes with NETWORK_REACHABLE=no "
                    "before network enablement and "
                    "NETWORK_REACHABLE=yes after enablement."
                ),
                "original_receipts":
                    snapshot_receipts(
                        Path("artifacts/live-003")
                    ),
            },
            {
                "experiment": "LIVE-004",
                "scope": "runs executed before network patch",
                "status": "SUPERSEDED",
                "benchmark_usable": False,
                "reason": "HARNESS_NETWORK_DISABLED",
                "detail": (
                    "Runs executed before CodexLiveRunner enabled "
                    "sandbox_workspace_write.network_access=true "
                    "are excluded from AFCR interpretation."
                ),
                "original_receipts":
                    snapshot_receipts(
                        Path("artifacts/live-004")
                    ),
            },
        ],
    }

    canonical = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    record["proof_sha256"] = hashlib.sha256(
        canonical
    ).hexdigest()

    path = out / "network-sandbox-supersession.json"

    path.write_text(
        json.dumps(
            record,
            indent=2,
            sort_keys=True,
        )
    )

    return path
