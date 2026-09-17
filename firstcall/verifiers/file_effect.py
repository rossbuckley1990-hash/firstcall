from __future__ import annotations

from pathlib import Path

from firstcall.hashutil import digest
from firstcall.model import Verification


class FileEffectVerifier:
    """Independent local verifier.

    The candidate is told to create a specific effect.
    FIRSTCALL checks it separately after the candidate exits.
    """

    def __init__(
        self,
        path: Path,
        expected: str,
    ):
        self.path = path
        self.expected = expected

    def verify(self) -> Verification:
        if not self.path.exists():
            return Verification(
                observed=False,
                evidence={
                    "path": str(self.path),
                    "exists": False,
                },
                reason="Expected effect absent",
            )

        actual = self.path.read_text()

        if actual != self.expected:
            return Verification(
                observed=False,
                evidence={
                    "path": str(self.path),
                    "exists": True,
                    "actual_sha256": digest(actual),
                    "expected_sha256": digest(
                        self.expected
                    ),
                },
                reason="Effect exists but is incorrect",
            )

        return Verification(
            observed=True,
            evidence={
                "path": str(self.path),
                "exists": True,
                "content_sha256": digest(actual),
            },
        )
