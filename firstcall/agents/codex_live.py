from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess
import time


@dataclass(frozen=True)
class AgentResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    events: tuple[dict, ...]


class CodexLiveRunner:
    def __init__(
        self,
        *,
        timeout: int = 300,
    ):
        executable = shutil.which("codex")

        if not executable:
            raise RuntimeError(
                "codex not found on PATH"
            )

        self.executable = executable
        self.timeout = timeout

    def run(
        self,
        *,
        cwd: Path,
        prompt: str,
        resend_key: str | None = None,
        subject: str | None = None,
        experiment_env: dict[str, str] | None = None,
    ) -> AgentResult:
        # Deliberately construct the environment instead
        # of passing os.environ wholesale.
        #
        # Only system/runtime variables plus the two
        # experiment variables are admitted.
        allowed_names = {
            "HOME",
            "PATH",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "TERM",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        }

        env = {
            key: value
            for key, value in os.environ.items()
            if key in allowed_names
        }

        if resend_key is not None:
            env["RESEND_API_KEY"] = resend_key

        if subject is not None:
            env["FIRSTCALL_SUBJECT"] = subject

        if experiment_env:
            for name, value in experiment_env.items():
                if not isinstance(name, str):
                    raise TypeError("experiment env name must be str")
                if not isinstance(value, str):
                    raise TypeError("experiment env value must be str")
                env[name] = value

        argv = [
            self.executable,
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "workspace-write",
            "-c",
            "sandbox_workspace_write.network_access=true",
            "--skip-git-repo-check",
            prompt,
        ]

        started = time.monotonic()

        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr

        except subprocess.TimeoutExpired as exc:
            exit_code = 124

            stdout = (
                exc.stdout
                if isinstance(exc.stdout, str)
                else ""
            )

            stderr = (
                exc.stderr
                if isinstance(exc.stderr, str)
                else ""
            )

            stderr += "\nFIRSTCALL_AGENT_TIMEOUT"

        duration_ms = int(
            (time.monotonic() - started) * 1000
        )

        events = []

        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(event, dict):
                events.append(event)

        return AgentResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            events=tuple(events),
        )
