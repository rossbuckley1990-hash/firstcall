from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from firstcall.claim import StructuredClaim, parse_claim


@dataclass(frozen=True)
class CommandEvidence:
    command: str
    exit_code: int | None
    output: str | None
    source: str


@dataclass(frozen=True)
class CodexEvidence:
    final_text: str
    claim: StructuredClaim
    candidate_commands: tuple[CommandEvidence, ...]
    candidate_execution_observed: bool
    candidate_exit_code: int | None


def _walk(value: Any):
    yield value

    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)

    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _strings(value: Any):
    for item in _walk(value):
        if isinstance(item, str):
            yield item


def _ints(value: Any):
    for item in _walk(value):
        if isinstance(item, int) and not isinstance(item, bool):
            yield item


def parse_jsonl(stdout: str) -> list[dict]:
    events = []

    for line in stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(event, dict):
            events.append(event)

    return events


def extract_final_text(events: list[dict]) -> str:
    """
    Codex JSON event schemas can evolve. Do not assume one exact
    nesting shape. Collect text-bearing strings from assistant-like
    events, preferring the last text containing FIRSTCALL_RESULT.
    """
    candidates: list[str] = []

    for event in events:
        blob = json.dumps(event).lower()

        if (
            "assistant" not in blob
            and "message" not in blob
            and "agent" not in blob
        ):
            continue

        for text in _strings(event):
            if text.startswith("FIRSTCALL_RESULT "):
                candidates.append(text)
            elif "FIRSTCALL_RESULT " in text:
                candidates.append(text)

    if not candidates:
        return ""

    for text in reversed(candidates):
        if "FIRSTCALL_RESULT " in text:
            return text

    return candidates[-1]


def _looks_like_candidate_command(text: str) -> bool:
    normalized = " ".join(text.split())

    patterns = (
        r"(^|\s)python3?\s+(\./)?integration\.py(\s|$)",
        r"(^|\s)[\"']?python3?[\"']?\s+"
        r"[\"']?(\./)?integration\.py[\"']?(\s|$)",
    )

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


def extract_candidate_commands(
    events: list[dict],
) -> tuple[CommandEvidence, ...]:
    """
    Parse the documented codex exec --json command_execution schema.

    Relevant completed event:

      {
        "type": "item.completed",
        "item": {
          "type": "command_execution",
          "command": "...",
          "aggregated_output": "...",
          "exit_code": 1,
          "status": "failed"
        }
      }

    Started events are deliberately not accepted as completion proof.
    Assistant prose is deliberately not execution proof.
    """
    found: list[CommandEvidence] = []

    for event in events:
        if event.get("type") != "item.completed":
            continue

        item = event.get("item")

        if not isinstance(item, dict):
            continue

        if item.get("type") != "command_execution":
            continue

        command = item.get("command")

        if not isinstance(command, str):
            continue

        if not _looks_like_candidate_command(command):
            continue

        exit_code = item.get("exit_code")

        if not isinstance(exit_code, int):
            exit_code = None

        output = item.get("aggregated_output")

        if not isinstance(output, str):
            output = None

        found.append(
            CommandEvidence(
                command=" ".join(command.split()),
                exit_code=exit_code,
                output=output,
                source="codex_jsonl:item.completed",
            )
        )

    return tuple(found)


def extract_codex_evidence(stdout: str) -> CodexEvidence:
    events = parse_jsonl(stdout)

    final_text = extract_final_text(events)

    # Formal claim may exist in final assistant text OR in captured
    # command output. Never infer it from arbitrary prose.
    claim = parse_claim(final_text)

    commands = extract_candidate_commands(events)

    if not claim.found:
        for command in commands:
            if not command.output:
                continue

            candidate_claim = parse_claim(command.output)

            if candidate_claim.found:
                claim = candidate_claim
                break

    exit_codes = [
        command.exit_code
        for command in commands
        if command.exit_code is not None
    ]

    candidate_exit = (
        exit_codes[-1]
        if exit_codes
        else None
    )

    return CodexEvidence(
        final_text=final_text,
        claim=claim,
        candidate_commands=commands,
        candidate_execution_observed=bool(commands),
        candidate_exit_code=candidate_exit,
    )


def extract_model_identity(jsonl_text: str) -> str | None:
    """
    Extract an explicit model identifier from Codex JSONL when Codex
    supplies one. Never infer a model from CLI version or prose.
    """
    import json

    model_keys = ("model", "model_name", "model_id")

    for raw in jsonl_text.splitlines():
        raw = raw.strip()
        if not raw:
            continue

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue

        stack = [event]

        while stack:
            obj = stack.pop()

            if isinstance(obj, dict):
                for key in model_keys:
                    value = obj.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()

                stack.extend(obj.values())

            elif isinstance(obj, list):
                stack.extend(obj)

    return None
