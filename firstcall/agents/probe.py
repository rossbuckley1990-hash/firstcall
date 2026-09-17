from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess


@dataclass(frozen=True)
class CLIProbe:
    executable: str
    path: str
    version: str
    help_text: str


def probe(executable: str) -> CLIProbe:
    path = shutil.which(executable)

    if not path:
        raise RuntimeError(
            f"{executable!r} not found on PATH"
        )

    version = subprocess.run(
        [path, "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    help_result = subprocess.run(
        [path, "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if version.returncode != 0:
        raise RuntimeError(
            f"{executable} --version failed: "
            f"{version.stderr.strip()}"
        )

    if help_result.returncode != 0:
        raise RuntimeError(
            f"{executable} --help failed: "
            f"{help_result.stderr.strip()}"
        )

    return CLIProbe(
        executable=executable,
        path=path,
        version=version.stdout.strip(),
        help_text=help_result.stdout,
    )
