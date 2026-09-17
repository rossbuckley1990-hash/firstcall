from __future__ import annotations

from dataclasses import asdict, is_dataclass
from hashlib import sha256
import json
from typing import Any


def normalise(value: Any) -> Any:
    if is_dataclass(value):
        return normalise(asdict(value))

    if isinstance(value, dict):
        return {
            str(k): normalise(v)
            for k, v in sorted(value.items())
        }

    if isinstance(value, (list, tuple)):
        return [normalise(v) for v in value]

    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        normalise(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def digest(value: Any) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()
