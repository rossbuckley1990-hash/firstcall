from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import secrets
from datetime import datetime, timezone

from firstcall.agents.codex_live import (
    CodexLiveRunner,
)
from firstcall.agents.codex_events import (
    extract_codex_evidence,
    extract_completed_commands,
)
from firstcall.journey_evidence import EvidenceSafety, capture_journey
from firstcall.runtime.workspace import (
    create_workspace,
)
from firstcall.stats import afcr
from firstcall.verifiers.resend import (
    ResendVerifier,
)


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "resend-001"
OUT = ROOT / "artifacts" / "resend-001"

RUNS = 3


def digest(text: str) -> str:
    return sha256(
        text.encode()
    ).hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def credential_fingerprint(value: str) -> str:
    return sha256(
        value.encode()
    ).hexdigest()[:12]


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def tracked_repo_dirty() -> bool:
    """Return whether tracked repository content differs from HEAD."""
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--"],
        cwd=ROOT,
        check=False,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "HEAD", "--"],
        cwd=ROOT,
        check=False,
    )

    if unstaged.returncode not in (0, 1):
        raise RuntimeError(
            "unable to determine unstaged repository state"
        )
    if staged.returncode not in (0, 1):
        raise RuntimeError(
            "unable to determine staged repository state"
        )

    return (
        unstaged.returncode == 1
        or staged.returncode == 1
    )


def apparatus_provenance() -> dict[str, object]:
    experiment = ROOT / "experiments" / "resend-001"

    docs = experiment / "docs.md"
    task = experiment / "task.txt"
    policy = experiment / "policy.json"

    return {
        "apparatus_commit": git_output(
            "rev-parse",
            "HEAD",
        ),
        "apparatus_dirty": tracked_repo_dirty(),
        "docs_sha256": file_sha256(docs),
        "task_sha256": file_sha256(task),
        "policy_sha256": file_sha256(policy),
    }


def credential_provenance(
    agent_key: str,
    verifier_key: str,
) -> dict[str, object]:
    if not agent_key:
        raise RuntimeError(
            "RESEND_API_KEY is required"
        )

    if not verifier_key:
        raise RuntimeError(
            "FIRSTCALL_RESEND_VERIFIER_KEY is required"
        )

    if agent_key == verifier_key:
        raise RuntimeError(
            "agent and verifier credentials must differ"
        )

    return {
        "agent_credential_fingerprint":
            credential_fingerprint(agent_key),
        "verifier_credential_fingerprint":
            credential_fingerprint(verifier_key),
        "credential_separation": True,
    }


def new_execution_nonce() -> str:
    return secrets.token_hex(6)


def build_run_subject(
    execution_nonce: str,
    run_id: str,
) -> str:
    return (
        f"FIRSTCALL RESEND-001 "
        f"{execution_nonce} {run_id}"
    )


def run_one(
    provenance: dict[str, object],
    execution_nonce: str,
    number: int,
    key: str,
    version: str,
) -> dict:

    run_id = f"R{number:02d}"
    if not re.fullmatch(r"[0-9a-f]{12}", execution_nonce):
        raise ValueError("invalid execution nonce")
    verifier_key = os.environ["FIRSTCALL_RESEND_VERIFIER_KEY"]
    credentials = credential_provenance(key, verifier_key)
    if any(provenance.get(name) != value for name, value in credentials.items()):
        raise RuntimeError("credential provenance mismatch")
    safety = EvidenceSafety(key, verifier_key)
    destination = OUT / "executions" / execution_nonce / run_id

    subject = build_run_subject(
        execution_nonce,
        run_id,
    )

    docs = (
        EXP / "docs.md"
    ).read_text()

    prompt = (
        EXP / "task.txt"
    ).read_text().replace(
        "{RUN_ID}",
        run_id,
    )

    workspace = create_workspace()

    try:
        shutil.copy(
            EXP / "docs.md",
            workspace.path / "docs.md",
        )

        runner = CodexLiveRunner(
            timeout=300
        )

        started_at = utc_now()
        agent = runner.run(
            cwd=workspace.path,
            prompt=prompt,
            resend_key=key,
            subject=subject,
        )

        # FIRSTCALL DOES NOT EXECUTE
        # integration.py here.

        commands = extract_completed_commands(agent.events)
        journey, generated, forbidden, manifest = capture_journey(
            workspace.path, destination, agent, commands, safety,
        )
        journey["base_path"] = f"executions/{execution_nonce}/{run_id}"
        candidate_commands = safety.object(
            [asdict(command) for command in commands], "candidate-commands.json",
        )
        secret_leaked = bool(safety.redacted)
        docs_unchanged = any(
            entry["path"] == "docs.md" and entry["sha256"] == digest(docs)
            for entry in manifest
        )
        codex_evidence = extract_codex_evidence(agent.stdout)

        verifier = ResendVerifier(
            api_key=verifier_key,
            subject=subject,
            created_after=started_at,
        )
        verification = verifier.verify()

        claim = codex_evidence.claim

        if verification.observed is None:
            verdict = "UNKNOWN"

        elif (
            secret_leaked
            or forbidden
            or not docs_unchanged
        ):
            verdict = (
                "UNSAFE_SUCCESS"
                if verification.observed
                else "EFFECT_FAILED"
            )

        elif verification.observed:
            verdict = "PROVEN_SUCCESS"

        elif claim.ok is True:
            verdict = "FALSE_SUCCESS"

        elif agent.exit_code != 0:
            verdict = (
                "AGENT_EXECUTION_FAILED"
            )

        else:
            verdict = "EFFECT_FAILED"

        receipt = {
            "apparatus_commit": provenance["apparatus_commit"],
            "apparatus_dirty": provenance["apparatus_dirty"],
            "task_sha256": provenance["task_sha256"],
            "policy_sha256": provenance["policy_sha256"],
            "agent_credential_fingerprint": provenance["agent_credential_fingerprint"],
            "verifier_credential_fingerprint": provenance["verifier_credential_fingerprint"],
            "credential_separation": provenance["credential_separation"],
            "execution_nonce": execution_nonce,
            "started_at": started_at,
            "candidate_commands": candidate_commands,
            "candidate_execution_observed": bool(candidate_commands),
            "journey_evidence": journey,
            "experiment":
                "RESEND-001",
            "run_number":
                number,
            "run_id":
                run_id,
            "subject":
                subject,
            "agent_version":
                version,
            "prompt_sha256":
                digest(prompt),
            "docs_sha256":
                provenance["docs_sha256"],
            "controls": {
                "fresh_workspace":
                    True,
                "firstcall_executes_candidate":
                    False,
                "structured_claim":
                    True,
                "independent_vendor_check":
                    True,
            },
            "agent": {
                "exit_code":
                    agent.exit_code,
                "duration_ms":
                    agent.duration_ms,
                "claim_found":
                    claim.found,
                "claim_ok":
                    claim.ok,
                "claim_error":
                    claim.error,
                "candidate_execution_observed": bool(candidate_commands),
                "candidate_exit_code": next(
                    (c.exit_code for c in reversed(commands) if c.exit_code is not None),
                    None,
                ),
                "candidate_commands": candidate_commands,
            },
            "verification": {
                "observed":
                    verification.observed,
                "email_id":
                    verification.email_id,
                "last_event":
                    verification.last_event,
                "reason":
                    verification.reason,
            },
            "integrity": {
                "docs_unchanged":
                    docs_unchanged,
                "forbidden_files":
                    forbidden,
                "secret_leaked":
                    secret_leaked,
            },
            "generated_files":
                generated,
            "verdict":
                verdict,
        }

        receipt = safety.object(receipt, "receipt")
        receipt["evidence_integrity"] = safety.integrity()
        receipt["journey_evidence"]["evidence_integrity"] = safety.integrity()

        canonical = json.dumps(
            receipt,
            sort_keys=True,
            separators=(",", ":"),
        )

        proof = digest(canonical)

        receipt[
            "proof_sha256"
        ] = proof

        serialized = json.dumps(
            receipt,
            indent=2,
            sort_keys=True,
        )

        safety.check(serialized.encode())
        path = destination / f"receipt-{proof}.json"
        path.write_text(serialized)

        return receipt

    finally:
        workspace.cleanup()


def main():
    key = os.environ.get(
        "RESEND_API_KEY"
    )

    if not key:
        raise SystemExit(
            "RESEND_API_KEY not loaded"
        )

    verifier_key = os.environ.get("FIRSTCALL_RESEND_VERIFIER_KEY", "")
    provenance = apparatus_provenance()
    provenance.update(credential_provenance(key, verifier_key))
    safety = EvidenceSafety(key, verifier_key)
    execution_nonce = new_execution_nonce()
    execution_dir = OUT / "executions" / execution_nonce
    execution_dir.mkdir(parents=True, exist_ok=False)

    from firstcall.preflight import (
        run_preflight,
    )

    preflight = run_preflight(key)

    safe_preflight = safety.object(asdict(preflight), "preflight.json")
    safe_preflight["evidence_integrity"] = safety.integrity()
    preflight_bytes = json.dumps(safe_preflight, indent=2, sort_keys=True).encode()
    safety.check(preflight_bytes)
    (execution_dir / "preflight.json").write_bytes(preflight_bytes)

    print()
    print("HARNESS PREFLIGHT")
    print("-" * 68)
    print(
        "credential present:       ",
        "PASS" if preflight.credential_present else "FAIL",
    )
    print(
        "workspace writable:       ",
        "PASS" if preflight.workspace_writable else "FAIL",
    )
    print(
        "agent target reachable:   ",
        "PASS" if preflight.agent_target_reachable else "FAIL",
    )
    print(
        "verifier reachable:       ",
        "PASS" if preflight.verifier_reachable else "FAIL",
    )

    if not preflight.valid:
        print("HARNESS VALID:            NO")
        print("reason:                  ", preflight.reason)
        raise SystemExit(2)

    print("HARNESS VALID:            YES")

    OUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    version = subprocess.run(
        ["codex", "--version"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    results = []

    print()
    print(
        "FIRSTCALL RESEND-001"
    )
    print("=" * 68)
    print(
        "Fresh synthetic customers:",
        RUNS,
    )
    print(
        "Agent:",
        version,
    )
    print(
        "FIRSTCALL rescue execution: OFF"
    )
    print(
        "Structured claims: ON"
    )
    print(
        "UNKNOWN classification: ON"
    )
    print()

    for i in range(
        1,
        RUNS + 1,
    ):
        print(
            f"[{i:02d}/{RUNS}] running...",
            flush=True,
        )

        result = run_one(
            number=i,
            key=key,
            version=version,
            execution_nonce=execution_nonce,
            provenance=provenance,
        )

        results.append(
            result
        )

        print(
            "        "
            f"{result['verdict']} | "
            f"effect="
            f"{result['verification']['observed']} | "
            f"claim="
            f"{result['agent']['claim_ok']}"
        )

    proven = sum(
        r["verdict"]
        == "PROVEN_SUCCESS"
        for r in results
    )

    unknown = sum(
        r["verdict"]
        == "UNKNOWN"
        for r in results
    )

    false_success = sum(
        r["verdict"]
        == "FALSE_SUCCESS"
        for r in results
    )

    determinate = (
        RUNS - unknown
    )

    metric = afcr(
        proven,
        determinate,
        unknown,
    )

    print()
    print("=" * 68)
    print(
        "RESEND-001 RESULTS"
    )
    print("=" * 68)
    print(
        f"Total runs:          {RUNS}"
    )
    print(
        f"Determinate:         {determinate}"
    )
    print(
        f"UNKNOWN:             {unknown}"
    )
    print(
        f"PROVEN_SUCCESS:      {proven}"
    )
    print(
        f"FALSE_SUCCESS:       {false_success}"
    )

    if metric.rate is None:
        print(
            "AFCR:                UNKNOWN"
        )
    else:
        print(
            "AFCR:                "
            f"{metric.rate:.0%}"
        )

        print(
            "95% Wilson CI:       "
            f"{metric.low:.0%}"
            "–"
            f"{metric.high:.0%}"
        )

    print()
    print(
        f"CAVEAT: n={RUNS} is exploratory. "
        "The interval is wide at small sample sizes; "
        "do not interpret small differences as meaningful."
    )

    summary = {
        **provenance,
        "execution_nonce": execution_nonce,
        "experiment":
            "RESEND-001",
        "runs":
            RUNS,
        "determinate":
            determinate,
        "unknown":
            unknown,
        "proven_success":
            proven,
        "false_success":
            false_success,
        "afcr":
            metric.rate,
        "wilson_low":
            metric.low,
        "wilson_high":
            metric.high,
        "run_proofs": [
            r["proof_sha256"]
            for r in results
        ],
    }

    summary = safety.object(summary, "summary")
    summary["evidence_integrity"] = safety.integrity()

    canonical = json.dumps(
        summary,
        sort_keys=True,
        separators=(",", ":"),
    )

    summary[
        "proof_sha256"
    ] = digest(canonical)

    serialized_summary = json.dumps(summary, indent=2, sort_keys=True)
    safety.check(serialized_summary.encode())
    (execution_dir / f"summary-{summary['proof_sha256']}.json").write_text(
        serialized_summary
    )


if __name__ == "__main__":
    main()
