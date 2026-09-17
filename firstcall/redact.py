from __future__ import annotations

import re


PATTERNS = (
    re.compile(r"sk_(?:test|live)_[A-Za-z0-9_-]+"),
    re.compile(r"\bre_[A-Za-z0-9-]{20,}\b"),
    re.compile(
        r"(?i)(api[_-]?key|secret|token)"
        r"""(\s*[:=]\s*['"]?)([^'"\s]+)"""
    ),
)


def redact(text: str) -> str:
    result = text

    for pattern in PATTERNS:
        if pattern.groups >= 3:
            result = pattern.sub(
                lambda m: (
                    f"{m.group(1)}"
                    f"{m.group(2)}"
                    "[REDACTED]"
                ),
                result,
            )
        else:
            result = pattern.sub(
                "[REDACTED]",
                result,
            )

    return result
