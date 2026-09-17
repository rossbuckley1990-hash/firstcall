from __future__ import annotations

from typing import Protocol

from firstcall.model import Verification


class Verifier(Protocol):
    def verify(self) -> Verification:
        ...
