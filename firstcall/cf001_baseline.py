from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from firstcall.verifiers.cf001 import verify_exactly_one_event

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "cf-001"
ART = ROOT / "artifacts" / "cf-001" / "baseline"
BASE_URL = "http://127.0.0.1:8765"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_proof(data: dict) -> str:
    body = dict(data)
    body.pop("proof_sha256", None)
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(raw)

def extract_event_id(text: str) -> str | None:
    hits = re.findall(r"evt_[A-Za-z0-9]+", text)
    return hits[-1] if hits else None

def extract_model(events: list[dict]) -> str | None:
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"model", "model_name", "model_id"} and isinstance(item, str):
                    return item
                found = walk(item)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = walk(item)
                if found:
                    return found
        return None

    for event in events:
        found = walk(event)
        if found:
            return found
    return None

def completed_commands(events: list[dict]) -> list[dict]:
    rows = []
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") != "command_execution":
            continue
        rows.append({
            "command": item.get("command"),
            "exit_code": item.get("exit_code"),
            "status": item.get("status"),
            "aggregated_output": item.get("aggregated_output"),
        })
    return rows

def run_one(run_id: str) -> dict:
    run_name = f"FIRSTCALL CF-001 {run_id}"
    workspace = Path(tempfile.mkdtemp(prefix=f"firstcall-{run_id.lower()}-"))

    try:
        subprocess.run(
            ["git", "init", "-q"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )

        docs = (EXP / "baseline-docs.md").read_text()
        base_task = (EXP / "task.txt").read_text()

        task = base_task.replace(
            "FIRSTCALL test event",
            run_name,
        )

        (workspace / "docs.md").write_text(docs)
        (workspace / "task.txt").write_text(task)

        before_docs = sha256_bytes((workspace / "docs.md").read_bytes())

        prompt = (
            "You are a fresh autonomous customer. "
            "Read docs.md and task.txt in the current directory. "
            "Complete the task yourself. "
            "You must write integration.py and execute it yourself. "
            "Do not inspect parent directories or the FIRSTCALL repository. "
            "Do not ask for help. "
            "Do not retry a failed product request. "
            "Your final response must include the required FIRSTCALL_RESULT line."
        )

        env = os.environ.copy()
        env["ACME_API_KEY"] = "FIRSTCALL_LOCAL_TOKEN"

        command = [
            "codex",
            "exec",
            "--json",
            "--sandbox",
            "workspace-write",
            "-c",
            "sandbox_workspace_write.network_access=true",
            prompt,
        ]

        started = time.time()

        proc = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

        duration = time.time() - started

        events = []
        for line in proc.stdout.splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

        thread_started = any(
            event.get("type") == "thread.started"
            for event in events
        )
        turn_started = any(
            event.get("type") == "turn.started"
            for event in events
        )
        turn_completed = any(
            event.get("type") == "turn.completed"
            for event in events
        )
        agent_started = thread_started and turn_started

        commands = completed_commands(events)

        all_output = "\n".join(
            [
                proc.stdout,
                proc.stderr,
                *[
                    str(row.get("aggregated_output") or "")
                    for row in commands
                ],
            ]
        )

        event_id = extract_event_id(all_output)

        if event_id:
            verification = verify_exactly_one_event(
                BASE_URL,
                event_id,
                run_name,
            )
        else:
            verification = {
                "observed": False,
                "status": None,
                "effect_id": None,
                "count": None,
                "cardinality_ok": False,
                "reason": "no_effect_id_observed",
            }

        integration = workspace / "integration.py"
        integration_exists = integration.exists()

        after_docs = sha256_bytes((workspace / "docs.md").read_bytes())
        docs_unchanged = before_docs == after_docs

        candidate_commands = [
            row for row in commands
            if "integration.py" in str(row.get("command") or "")
        ]

        candidate_executed = bool(candidate_commands)

        candidate_exit = (
            candidate_commands[-1].get("exit_code")
            if candidate_commands
            else None
        )

        if not agent_started:
            verdict = "UNKNOWN"
            invalid_reason = "agent_launch_failed"
        elif verification.get("observed") is True and candidate_executed and candidate_exit == 0 and docs_unchanged:
            verdict = "PROVEN_SUCCESS"
            invalid_reason = None
        elif candidate_executed and candidate_exit not in {0, None}:
            verdict = "EXECUTION_FAILED"
            invalid_reason = None
        else:
            verdict = "EFFECT_FAILED"
            invalid_reason = None

        manifest = json.loads((EXP / "baseline-manifest.json").read_text())

        receipt = {
            "schema": "firstcall.cf001-baseline-receipt.v1",
            "experiment": "CF-001",
            "phase": "baseline",
            "run_id": run_id,
            "run_name": run_name,
            "manifest_sha256": manifest["manifest_sha256"],
            "controls": {
                "fresh_workspace": True,
                "firstcall_executes_candidate": False,
                "rerun": False,
                "agent_visible_files": ["docs.md", "task.txt"],
                "docs_unchanged": docs_unchanged,
            },
            "agent": {
                "provider": "Codex",
                "thread_started": thread_started,
                "turn_started": turn_started,
                "turn_completed": turn_completed,
                "agent_started": agent_started,
                "cli_version": manifest["agent"]["cli_version"],
                "model": extract_model(events),
                "model_identity_status": "observed" if extract_model(events) else "unknown",
                "process_exit_code": proc.returncode,
                "duration_seconds": round(duration, 3),
            },
            "execution": {
                "integration_exists": integration_exists,
                "candidate_execution_observed": candidate_executed,
                "candidate_exit_code": candidate_exit,
                "candidate_commands": candidate_commands,
            },
            "verification": verification,
            "invalid_reason": invalid_reason,
            "verdict": verdict,
        }

        receipt["proof_sha256"] = canonical_proof(receipt)

        ART.mkdir(parents=True, exist_ok=True)

        trace_dir = ART / "traces" / run_id
        trace_dir.mkdir(parents=True, exist_ok=True)

        (trace_dir / "codex.stdout.jsonl").write_text(proc.stdout)
        (trace_dir / "codex.stderr.txt").write_text(proc.stderr)

        evidence_workspace = trace_dir / "workspace"
        if evidence_workspace.exists():
            shutil.rmtree(evidence_workspace)

        shutil.copytree(
            workspace,
            evidence_workspace,
            ignore=shutil.ignore_patterns(".git"),
        )

        out = ART / f"{run_id}.json"
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

        check = json.loads(out.read_text())
        assert check["proof_sha256"] == canonical_proof(check)

        print(
            run_id,
            verdict,
            "candidate_exit=",
            candidate_exit,
            "effect=",
            verification.get("observed"),
            "count=",
            verification.get("count"),
            "model=",
            receipt["agent"]["model"],
        )

        return receipt

    finally:
        shutil.rmtree(workspace, ignore_errors=True)

def main():
    ART.mkdir(parents=True, exist_ok=True)

    existing = [
        ART / f"B0{i}.json"
        for i in range(1, 4)
        if (ART / f"B0{i}.json").exists()
    ]

    if existing:
        raise SystemExit(
            "REFUSING TO RUN: baseline receipt already exists: "
            + ", ".join(str(p) for p in existing)
        )

    results = []

    for run_id in ("B01", "B02", "B03"):
        results.append(run_one(run_id))

    determinate = [
        r for r in results
        if r["verdict"] != "UNKNOWN"
    ]

    successes = sum(
        r["verdict"] == "PROVEN_SUCCESS"
        for r in determinate
    )

    summary = {
        "schema": "firstcall.cf001-baseline-summary.v1",
        "experiment": "CF-001",
        "runs": len(results),
        "determinate": len(determinate),
        "proven_successes": successes,
        "afcr": (
            successes / len(determinate)
            if determinate
            else None
        ),
        "run_proofs": {
            r["run_id"]: r["proof_sha256"]
            for r in results
        },
    }

    summary["proof_sha256"] = canonical_proof(summary)

    (ART / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    print(json.dumps(summary, indent=2))
    print("CF-001 BASELINE COMPLETE")

if __name__ == "__main__":
    main()
