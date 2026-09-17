from __future__ import annotations

import re

from firstcall.model import HygieneFinding


SECRET_PATTERNS = (
    re.compile(r"sk_(?:test|live)_[A-Za-z0-9_-]+"),
    re.compile(r"re_[A-Za-z0-9_-]{12,}"),
)


def scan_files(
    files: dict[str, str],
) -> tuple[HygieneFinding, ...]:
    findings: list[HygieneFinding] = []

    for path, content in files.items():
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append(
                    HygieneFinding(
                        rule="credential_in_generated_file",
                        severity="critical",
                        evidence=path,
                    )
                )

    return tuple(findings)
