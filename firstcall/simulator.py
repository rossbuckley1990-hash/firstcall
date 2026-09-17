from __future__ import annotations

from firstcall.grade import grade
from firstcall.hashutil import digest
from firstcall.hygiene import scan_files
from firstcall.model import (
    Execution,
    RunResult,
    Verification,
)


def simulated_run(
    *,
    run_id: str,
    effect_exists: bool,
    exit_code: int = 0,
    stdout: str = "success",
    files: dict[str, str] | None = None,
) -> RunResult:
    generated = files or {
        "main.py": "print('hello')"
    }

    execution = Execution(
        exit_code=exit_code,
        stdout=stdout,
        stderr="",
        generated_files=generated,
    )

    verification = Verification(
        observed=effect_exists,
        evidence={
            "verifier": "simulator",
            "effect_exists": effect_exists,
        },
        reason=None if effect_exists else (
            "Independent effect not observed"
        ),
    )

    hygiene = scan_files(generated)

    outcome = grade(
        execution,
        verification,
        hygiene,
    )

    return RunResult(
        run_id=run_id,
        task_id="stripe:t1",
        agent="simulated-agent",
        agent_version="0",
        docs_sha256=digest("docs"),
        container_sha256=digest("container"),
        prompt_sha256=digest("prompt"),
        execution=execution,
        verification=verification,
        hygiene=hygiene,
        outcome=outcome,
    )
