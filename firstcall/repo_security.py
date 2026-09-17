from __future__ import annotations

from pathlib import Path
import re


# These are deliberately conservative repository checks.
# Unit tests containing synthetic credentials are excluded because
# those fixtures exist specifically to test redaction/hygiene logic.
SECRET_PATTERNS = (
    re.compile(rb"sk_(?:live|test)_[A-Za-z0-9_-]{20,}"),
    re.compile(rb"re_[A-Za-z0-9_-]{20,}"),
)

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
}

EXCLUDED_TEST_FILES = {
    "test_kernel.py",
    "test_runtime.py",
}


def scan_repository(root: Path) -> list[str]:
    hits: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(root)

        if any(
            part in EXCLUDED_PARTS
            for part in relative.parts
        ):
            continue

        if (
            "tests" in relative.parts
            and path.name in EXCLUDED_TEST_FILES
        ):
            continue

        try:
            data = path.read_bytes()
        except OSError:
            continue

        if any(
            pattern.search(data)
            for pattern in SECRET_PATTERNS
        ):
            hits.append(str(relative))

    return sorted(set(hits))
