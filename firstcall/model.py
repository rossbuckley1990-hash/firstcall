from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Outcome(str, Enum):
    PROVEN_SUCCESS = "PROVEN_SUCCESS"
    FALSE_SUCCESS = "FALSE_SUCCESS"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EFFECT_FAILED = "EFFECT_FAILED"
    UNSAFE_SUCCESS = "UNSAFE_SUCCESS"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Task:
    task_id: str
    prompt: str
    target: str


@dataclass(frozen=True)
class Execution:
    exit_code: int
    stdout: str
    stderr: str
    generated_files: dict[str, str]


@dataclass(frozen=True)
class Verification:
    observed: bool
    evidence: dict[str, Any]
    reason: str | None = None


@dataclass(frozen=True)
class HygieneFinding:
    rule: str
    severity: str
    evidence: str


@dataclass(frozen=True)
class RunResult:
    run_id: str
    task_id: str
    agent: str
    agent_version: str
    docs_sha256: str
    container_sha256: str
    prompt_sha256: str
    execution: Execution
    verification: Verification
    hygiene: tuple[HygieneFinding, ...]
    outcome: Outcome
    metadata: dict[str, Any] = field(default_factory=dict)
