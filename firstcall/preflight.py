from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request


@dataclass(frozen=True)
class PreflightResult:
    credential_present: bool
    workspace_writable: bool
    agent_target_reachable: bool
    verifier_reachable: bool
    agent_exit_code: int
    valid: bool
    reason: str | None


def verifier_reachable(api_key: str) -> bool:
    """
    This is a health check, not an effect check.

    HTTP 4xx still proves DNS/TLS/HTTP reachability unless
    authentication itself prevents the verifier from functioning.
    """
    req = urllib.request.Request(
        "https://api.resend.com/emails?limit=1",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "firstcall-preflight/0.1",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as exc:
        # Authentication/rate-limit failures mean the verifier
        # is not healthy enough for a benchmark.
        if exc.code in {401, 403, 429}:
            return False
        return True
    except Exception:
        return False


def run_codex_preflight(
    *,
    api_key: str,
    timeout: int = 60,
) -> tuple[bool, int]:
    codex = shutil.which("codex")

    if not codex:
        return False, 127

    prompt = (
        "Do not create or modify files. "
        "Do not send an email. "
        "Check whether RESEND_API_KEY exists without printing it. "
        "Attempt HTTPS connectivity to https://api.resend.com. "
        "Output exactly these two lines with yes/no values:\n"
        "KEY_PRESENT <yes/no>\n"
        "NETWORK_REACHABLE <yes/no>"
    )

    allowed = {
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
        name: value
        for name, value in os.environ.items()
        if name in allowed
    }

    env["RESEND_API_KEY"] = api_key

    with tempfile.TemporaryDirectory(
        prefix="firstcall-preflight-"
    ) as tmp:
        result = subprocess.run(
            [
                codex,
                "exec",
                "--ephemeral",
                "--sandbox",
                "workspace-write",
                "-c",
                "sandbox_workspace_write.network_access=true",
                "--skip-git-repo-check",
                prompt,
            ],
            cwd=tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    combined = result.stdout + "\n" + result.stderr

    passed = (
        "KEY_PRESENT yes" in combined
        and "NETWORK_REACHABLE yes" in combined
        and api_key not in combined
    )

    return passed, result.returncode


def run_preflight(api_key: str) -> PreflightResult:
    credential = bool(api_key)

    with tempfile.TemporaryDirectory(
        prefix="firstcall-write-"
    ) as tmp:
        probe = Path(tmp) / "probe"
        try:
            probe.write_text("ok")
            writable = probe.read_text() == "ok"
        except Exception:
            writable = False

    if credential:
        try:
            agent_network, exit_code = run_codex_preflight(
                api_key=api_key
            )
        except Exception:
            agent_network = False
            exit_code = 125

        verifier = verifier_reachable(api_key)
    else:
        agent_network = False
        verifier = False
        exit_code = 126

    failures = []

    if not credential:
        failures.append("CREDENTIAL_MISSING")

    if not writable:
        failures.append("WORKSPACE_NOT_WRITABLE")

    if not agent_network:
        failures.append("TARGET_NETWORK_UNAVAILABLE")

    if not verifier:
        failures.append("VERIFIER_UNAVAILABLE")

    return PreflightResult(
        credential_present=credential,
        workspace_writable=writable,
        agent_target_reachable=agent_network,
        verifier_reachable=verifier,
        agent_exit_code=exit_code,
        valid=not failures,
        reason=",".join(failures) if failures else None,
    )


def write_preflight_receipt(
    result: PreflightResult,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            asdict(result),
            indent=2,
            sort_keys=True,
        )
    )
