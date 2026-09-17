from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil

from firstcall.runtime.process import execute, ProcessResult


@dataclass(frozen=True)
class CodexRun:
    process: ProcessResult
    events: tuple[dict, ...]
    final_output: str


class CodexRunner:
    def __init__(
        self,
        *,
        model: str | None = None,
        timeout: int = 300,
    ):
        self.executable = shutil.which("codex")
        if not self.executable:
            raise RuntimeError("codex not found on PATH")

        self.model = model
        self.timeout = timeout

    def run(
        self,
        *,
        prompt: str,
        cwd: Path,
    ) -> CodexRun:
        argv = [
            self.executable,
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "workspace-write",
            "--skip-git-repo-check",
        ]

        if self.model:
            argv += ["--model", self.model]

        argv.append(prompt)

        result = execute(
            argv,
            cwd=cwd,
            timeout=self.timeout,
        )

        events = []

        for line in result.stdout.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(value, dict):
                events.append(value)

        final_output = ""

        # Keep this deliberately tolerant of event schema changes.
        for event in reversed(events):
            for key in (
                "message",
                "text",
                "output_text",
                "content",
            ):
                value = event.get(key)

                if isinstance(value, str):
                    final_output = value
                    break

            if final_output:
                break

        return CodexRun(
            process=result,
            events=tuple(events),
            final_output=final_output,
        )
