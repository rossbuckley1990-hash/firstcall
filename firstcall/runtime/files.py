from __future__ import annotations

from hashlib import sha256
from pathlib import Path


def snapshot_tree(
    root: Path,
) -> dict[str, dict[str, str | int]]:
    result: dict[
        str,
        dict[str, str | int],
    ] = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        relative = str(
            path.relative_to(root)
        )

        data = path.read_bytes()

        result[relative] = {
            "sha256": sha256(data).hexdigest(),
            "bytes": len(data),
        }

    return result


def read_text_files(
    root: Path,
    *,
    max_bytes: int = 1_000_000,
) -> dict[str, str]:
    result: dict[str, str] = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        data = path.read_bytes()

        if len(data) > max_bytes:
            continue

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue

        result[
            str(path.relative_to(root))
        ] = text

    return result
