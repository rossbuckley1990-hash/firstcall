from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time


@dataclass(frozen=True)
class ProcessResult:
    argv: tuple[str, ...]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


def execute(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 120,
) -> ProcessResult:
    started = time.monotonic()

    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        duration = int(
            (time.monotonic() - started) * 1000
        )

        return ProcessResult(
            argv=tuple(argv),
            cwd=str(cwd),
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=duration,
        )

    except subprocess.TimeoutExpired as exc:
        duration = int(
            (time.monotonic() - started) * 1000
        )

        return ProcessResult(
            argv=tuple(argv),
            cwd=str(cwd),
            exit_code=124,
            stdout=(
                exc.stdout
                if isinstance(exc.stdout, str)
                else ""
            ),
            stderr=(
                exc.stderr
                if isinstance(exc.stderr, str)
                else ""
            )
            + "\nFIRSTCALL_TIMEOUT",
            duration_ms=duration,
        )
