from __future__ import annotations

from dataclasses import dataclass
import json


PREFIX = "FIRSTCALL_RESULT "


@dataclass(frozen=True)
class StructuredClaim:
    found: bool
    ok: bool | None
    payload: dict | None
    error: str | None


def parse_claim(text: str) -> StructuredClaim:
    matches = [
        line[len(PREFIX):].strip()
        for line in text.splitlines()
        if line.startswith(PREFIX)
    ]

    if not matches:
        return StructuredClaim(
            found=False,
            ok=None,
            payload=None,
            error="structured claim absent",
        )

    raw = matches[-1]

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return StructuredClaim(
            found=True,
            ok=None,
            payload=None,
            error="invalid structured claim JSON",
        )

    ok = payload.get("ok")

    if not isinstance(ok, bool):
        return StructuredClaim(
            found=True,
            ok=None,
            payload=payload,
            error="claim field 'ok' must be boolean",
        )

    return StructuredClaim(
        found=True,
        ok=ok,
        payload=payload,
        error=None,
    )
