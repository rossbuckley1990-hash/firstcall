from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(data: Any) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def proof_sha256(data: dict) -> str:
    unsigned = dict(data)
    unsigned.pop("proof_sha256", None)
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def verify_receipt(path: Path) -> tuple[bool, str, str]:
    data = json.loads(path.read_text())
    recorded = data.get("proof_sha256")

    if not isinstance(recorded, str):
        return False, "", ""

    calculated = proof_sha256(data)
    return recorded == calculated, recorded, calculated
