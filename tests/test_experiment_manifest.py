from firstcall.experiment_manifest import (
    build_manifest,
    manifest_sha256,
)


def test_manifest_is_content_addressed(tmp_path):
    docs = tmp_path / "docs.md"
    task = tmp_path / "task.txt"

    docs.write_text("docs")
    task.write_text("task")

    a = build_manifest(
        experiment="LIVE-X",
        docs_path=docs,
        task_path=task,
        runs=1,
        provider="resend",
        verifier="resend",
    )

    b = build_manifest(
        experiment="LIVE-X",
        docs_path=docs,
        task_path=task,
        runs=1,
        provider="resend",
        verifier="resend",
    )

    assert manifest_sha256(a) == manifest_sha256(b)


def test_manifest_changes_when_docs_change(tmp_path):
    docs = tmp_path / "docs.md"
    task = tmp_path / "task.txt"

    docs.write_text("docs-v1")
    task.write_text("task")

    a = build_manifest(
        experiment="LIVE-X",
        docs_path=docs,
        task_path=task,
        runs=1,
        provider="resend",
        verifier="resend",
    )

    docs.write_text("docs-v2")

    b = build_manifest(
        experiment="LIVE-X",
        docs_path=docs,
        task_path=task,
        runs=1,
        provider="resend",
        verifier="resend",
    )

    assert manifest_sha256(a) != manifest_sha256(b)
