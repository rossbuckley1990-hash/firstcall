import os
import sys

from firstcall.runtime.files import (
    read_text_files,
    snapshot_tree,
)
from firstcall.runtime.process import execute
from firstcall.runtime.workspace import (
    create_workspace,
)
from firstcall.verifiers.file_effect import (
    FileEffectVerifier,
)


def test_workspace_is_fresh():
    a = create_workspace()
    b = create_workspace()

    try:
        assert a.path != b.path
        assert list(a.path.iterdir()) == []
        assert list(b.path.iterdir()) == []
    finally:
        a.cleanup()
        b.cleanup()


def test_process_executes_in_workspace():
    workspace = create_workspace()

    try:
        result = execute(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path;"
                    "Path('effect.txt').write_text('42')"
                ),
            ],
            cwd=workspace.path,
            env=os.environ.copy(),
        )

        assert result.exit_code == 0
        assert (
            workspace.path / "effect.txt"
        ).read_text() == "42"
    finally:
        workspace.cleanup()


def test_external_verifier_does_not_trust_stdout():
    workspace = create_workspace()

    try:
        result = execute(
            [
                sys.executable,
                "-c",
                "print('SUCCESS everything worked')",
            ],
            cwd=workspace.path,
            env=os.environ.copy(),
        )

        assert result.exit_code == 0
        assert "SUCCESS" in result.stdout

        verification = FileEffectVerifier(
            workspace.path / "effect.txt",
            "42",
        ).verify()

        assert verification.observed is False
    finally:
        workspace.cleanup()


def test_external_verifier_observes_real_effect():
    workspace = create_workspace()

    try:
        execute(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path;"
                    "Path('effect.txt').write_text('42')"
                ),
            ],
            cwd=workspace.path,
            env=os.environ.copy(),
        )

        verification = FileEffectVerifier(
            workspace.path / "effect.txt",
            "42",
        ).verify()

        assert verification.observed is True
    finally:
        workspace.cleanup()


def test_tree_snapshot_detects_files():
    workspace = create_workspace()

    try:
        (workspace.path / "a.txt").write_text(
            "hello"
        )

        tree = snapshot_tree(workspace.path)

        assert "a.txt" in tree
        assert len(tree["a.txt"]["sha256"]) == 64
    finally:
        workspace.cleanup()


def test_text_capture_ignores_binary():
    workspace = create_workspace()

    try:
        (workspace.path / "a.txt").write_text(
            "hello"
        )
        (workspace.path / "binary.bin").write_bytes(
            b"\xff\xfe\x00"
        )

        files = read_text_files(workspace.path)

        assert files == {"a.txt": "hello"}
    finally:
        workspace.cleanup()
