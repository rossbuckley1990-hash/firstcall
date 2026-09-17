from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass
class FreshWorkspace:
    _tmp: tempfile.TemporaryDirectory[str]

    @property
    def path(self) -> Path:
        return Path(self._tmp.name)

    def cleanup(self) -> None:
        self._tmp.cleanup()


def create_workspace() -> FreshWorkspace:
    tmp = tempfile.TemporaryDirectory(
        prefix="firstcall-run-"
    )

    return FreshWorkspace(tmp)
