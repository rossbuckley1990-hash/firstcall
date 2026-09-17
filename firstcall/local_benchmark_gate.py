from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from firstcall.benchmark_evidence import (
    build_benchmark_receipt,
    write_benchmark_receipt,
)
from firstcall.claim import parse_claim
from firstcall.receipt_verify import verify_receipt


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        docs = root / "docs.md"
        task = root / "task.txt"
        integration = root / "integration.py"
        effect = root / "effect.json"

        docs.write_text(
            "LOCAL PRODUCT\n"
            "Write the required effect to effect.json.\n"
        )

        task.write_text(
            "Execute integration.py and create the "
            "documented product effect.\n"
        )

        docs_before = docs.read_bytes()

        integration.write_text(
            "import json\n"
            "from pathlib import Path\n"
            "\n"
            "Path('effect.json').write_text("
            "json.dumps({'created': True, 'value': 42}))\n"
            "\n"
            "print('FIRSTCALL_RESULT ' + "
            "json.dumps({'ok': True, 'stage': 'complete'}, "
            "separators=(',', ':')))\n"
        )

        proc = subprocess.run(
            ["python", "integration.py"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

        claim = parse_claim(proc.stdout)

        observed = False
        effect_id = None

        if effect.exists():
            payload = json.loads(
                effect.read_text()
            )

            observed = (
                payload.get("created") is True
                and payload.get("value") == 42
            )

            if observed:
                effect_id = "local-effect-42"

        docs_unchanged = (
            docs.read_bytes() == docs_before
        )

        command = {
            "command": "python integration.py",
            "exit_code": proc.returncode,
            "output": proc.stdout,
            "source": "local_control",
        }

        claim_dict = {
            "found": claim.found,
            "ok": claim.ok,
            "payload": claim.payload,
        }

        verification = {
            "observed": observed,
            "reason": (
                None
                if observed
                else "expected local effect absent"
            ),
            "effect_id": effect_id,
        }

        if (
            proc.returncode == 0
            and claim.ok is True
            and observed
        ):
            verdict = "PROVEN_SUCCESS"
        elif claim.ok is True and not observed:
            verdict = "FALSE_SUCCESS"
        elif proc.returncode != 0:
            verdict = "EXECUTION_FAILED"
        else:
            verdict = "EFFECT_FAILED"

        receipt = build_benchmark_receipt(
            experiment="LOCAL-BENCHMARK-001",
            run_number=1,
            docs_path=docs,
            task_path=task,
            provider="local",
            verifier="local-file-effect",
            agent_version="local-control",
            model=None,
            candidate_execution_observed=True,
            candidate_exit_code=proc.returncode,
            candidate_commands=[command],
            claim=claim_dict,
            verification=verification,
            verdict=verdict,
            docs_unchanged=docs_unchanged,
            forbidden_files=[],
            secret_leaked=False,
        )

        out = Path(
            "artifacts/local-benchmark-001/"
            "01-receipt.json"
        )

        write_benchmark_receipt(
            receipt,
            out,
        )

        ok, recorded, calculated = (
            verify_receipt(out)
        )

        print(
            "FIRSTCALL v0.3 LOCAL "
            "BENCHMARK EVIDENCE GATE"
        )
        print("=" * 60)

        print(
            "candidate execution observed:",
            receipt["execution"]
            ["candidate_execution_observed"],
        )

        print(
            "candidate exit:",
            receipt["execution"]
            ["candidate_exit_code"],
        )

        print(
            "claim found:",
            receipt["claim"]["found"],
        )

        print(
            "claim ok:",
            receipt["claim"]["ok"],
        )

        print(
            "vendor/effect observed:",
            receipt["verification"]["observed"],
        )

        print(
            "docs unchanged:",
            receipt["integrity"]["docs_unchanged"],
        )

        print(
            "secret leaked:",
            receipt["integrity"]["secret_leaked"],
        )

        print(
            "model:",
            receipt["agent"]["model"],
        )

        print(
            "model identity status:",
            receipt["agent"]
            ["model_identity_status"],
        )

        print(
            "manifest hash:",
            receipt["manifest_sha256"],
        )

        print(
            "proof recorded:",
            recorded,
        )

        print(
            "proof calculated:",
            calculated,
        )

        print(
            "receipt self-verifies:",
            ok,
        )

        print(
            "verdict:",
            receipt["verdict"],
        )

        assert (
            receipt["execution"]
            ["candidate_execution_observed"]
            is True
        )

        assert (
            receipt["execution"]
            ["candidate_exit_code"]
            == 0
        )

        assert receipt["claim"]["found"] is True
        assert receipt["claim"]["ok"] is True

        assert (
            receipt["verification"]["observed"]
            is True
        )

        assert (
            receipt["integrity"]["docs_unchanged"]
            is True
        )

        assert (
            receipt["integrity"]["secret_leaked"]
            is False
        )

        assert (
            receipt["controls"]
            ["firstcall_executes_candidate"]
            is False
        )

        assert (
            receipt["agent"]
            ["model_identity_status"]
            == "unknown"
        )

        assert ok is True

        assert (
            receipt["verdict"]
            == "PROVEN_SUCCESS"
        )

        print()
        print(
            "LOCAL BENCHMARK EVIDENCE: PASS"
        )


if __name__ == "__main__":
    main()
