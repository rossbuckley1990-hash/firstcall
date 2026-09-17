import json

from firstcall.benchmark_evidence import (
    build_benchmark_receipt,
    write_benchmark_receipt,
)
from firstcall.experiment_manifest import (
    manifest_sha256,
)
from firstcall.receipt_verify import (
    verify_receipt,
)


def make_receipt(tmp_path, model=None):
    docs = tmp_path / "docs.md"
    task = tmp_path / "task.txt"

    docs.write_text("Official integration docs v1")
    task.write_text("Create and execute integration.py")

    return build_benchmark_receipt(
        experiment="LOCAL-001",
        run_number=1,
        docs_path=docs,
        task_path=task,
        provider="local",
        verifier="file-effect",
        agent_version="codex-test",
        model=model,
        candidate_execution_observed=True,
        candidate_exit_code=0,
        candidate_commands=[
            {
                "command": "python integration.py",
                "exit_code": 0,
                "output":
                    'FIRSTCALL_RESULT '
                    '{"ok":true,"stage":"complete"}\n',
                "source":
                    "codex_jsonl:item.completed",
            }
        ],
        claim={
            "found": True,
            "ok": True,
            "payload": {
                "ok": True,
                "stage": "complete",
            },
        },
        verification={
            "observed": True,
            "reason": None,
            "effect_id": "local-effect-1",
        },
        verdict="PROVEN_SUCCESS",
        docs_unchanged=True,
        forbidden_files=[],
        secret_leaked=False,
    )


def test_receipt_contains_complete_evidence(tmp_path):
    receipt = make_receipt(
        tmp_path,
        model="gpt-test-model",
    )

    assert receipt["schema"] == (
        "firstcall.benchmark-receipt.v1"
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
        receipt["controls"]
        ["firstcall_executes_candidate"]
        is False
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
        receipt["agent"]["model"]
        == "gpt-test-model"
    )

    assert (
        receipt["agent"]["model_identity_status"]
        == "observed"
    )


def test_unknown_model_is_not_inferred(tmp_path):
    receipt = make_receipt(
        tmp_path,
        model=None,
    )

    assert receipt["agent"]["model"] is None

    assert (
        receipt["agent"]["model_identity_status"]
        == "unknown"
    )


def test_manifest_hash_is_valid(tmp_path):
    receipt = make_receipt(tmp_path)

    assert receipt["manifest_sha256"] == (
        manifest_sha256(receipt["manifest"])
    )


def test_written_receipt_self_verifies(tmp_path):
    receipt = make_receipt(tmp_path)

    path = tmp_path / "receipt.json"

    write_benchmark_receipt(
        receipt,
        path,
    )

    ok, recorded, calculated = (
        verify_receipt(path)
    )

    assert ok is True
    assert recorded == calculated


def test_tampering_breaks_proof(tmp_path):
    receipt = make_receipt(tmp_path)

    path = tmp_path / "receipt.json"

    write_benchmark_receipt(
        receipt,
        path,
    )

    data = json.loads(path.read_text())

    data["verdict"] = "EFFECT_FAILED"

    path.write_text(
        json.dumps(data)
    )

    ok, _, _ = verify_receipt(path)

    assert ok is False


def test_docs_change_changes_manifest(tmp_path):
    docs = tmp_path / "docs.md"
    task = tmp_path / "task.txt"

    docs.write_text("docs v1")
    task.write_text("task")

    kwargs = dict(
        experiment="LOCAL-001",
        run_number=1,
        docs_path=docs,
        task_path=task,
        provider="local",
        verifier="local",
        agent_version="test",
        model=None,
        candidate_execution_observed=True,
        candidate_exit_code=0,
        candidate_commands=[],
        claim={
            "found": True,
            "ok": True,
            "payload": {"ok": True},
        },
        verification={
            "observed": True,
        },
        verdict="PROVEN_SUCCESS",
        docs_unchanged=True,
        forbidden_files=[],
        secret_leaked=False,
    )

    first = build_benchmark_receipt(**kwargs)

    docs.write_text("docs v2")

    second = build_benchmark_receipt(**kwargs)

    assert (
        first["manifest_sha256"]
        != second["manifest_sha256"]
    )
