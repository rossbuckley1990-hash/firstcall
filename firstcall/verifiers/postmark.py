from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import json
import math
import re
import subprocess
import time
from typing import Any


@dataclass(frozen=True)
class PostmarkObservation:
    observed: bool
    message_id: str | None
    subject: str | None
    recipient: str | None
    status: str | None
    reason: str


class PostmarkVerifier:
    """
    Independent Postmark vendor-side verifier.

    Verification requires exactly one matching outbound message created
    at or after the current FIRSTCALL run boundary. An optional candidate ID
    constrains independent evidence; it is never evidence itself. By default,
    observe immediately, then after each of two five-second waits. Return on
    success or conclusive unsafe/malformed evidence. Each request has a ten-
    second timeout (at most 40 seconds of requests + waits, plus local overhead).
    No send is performed. Historical cohort pins must not be updated to this
    changed measurement protocol.
    """

    def __init__(
        self,
        *,
        server_token: str,
        subject: str,
        recipient: str,
        created_after: str,
        attempts: int = 3,
        retry_delay: float = 5.0,
        wait: Callable[[float], None] | None = None,
        expected_message_id: str | None = None,
    ) -> None:
        if type(attempts) is not int or attempts < 1:
            raise ValueError("attempts must be a positive integer")
        if not math.isfinite(retry_delay) or retry_delay <= 0:
            raise ValueError("retry_delay must be finite and positive")
        if expected_message_id is not None and (
            not isinstance(expected_message_id, str)
            or re.fullmatch(
                r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}",
                expected_message_id,
            ) is None
        ):
            raise ValueError("expected_message_id must be a canonical UUID")
        self.expected_message_id = (
            expected_message_id.lower() if expected_message_id is not None else None
        )
        self.retry_delay = retry_delay
        self.wait = wait if wait is not None else time.sleep
        self.server_token = server_token
        self.subject = subject
        self.recipient = recipient
        self.created_after = created_after
        self.attempts = attempts

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError("Postmark timestamps require a timezone")
        return parsed

    def _list(self) -> dict[str, Any]:
        completed = subprocess.run(
            [
                "curl",
                "-sS",
                "--fail-with-body",
                "--max-time",
                "10",
                "-H",
                (
                    "X-Postmark-Server-Token: "
                    + self.server_token
                ),
                (
                    "https://api.postmarkapp.com/"
                    "messages/outbound"
                    "?count=100&offset=0"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                "Postmark verification request failed"
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Postmark verifier received invalid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise RuntimeError(
                "Postmark verifier received malformed response"
            )

        return payload

    def _failure(self, reason: str) -> PostmarkObservation:
        return PostmarkObservation(
            False, None, self.subject, self.recipient, None, reason,
        )

    def verify(self) -> PostmarkObservation:
        boundary = self._parse_time(
            self.created_after
        )

        last_reason = "vendor effect not observed"

        for attempt in range(self.attempts):
            if attempt:
                self.wait(self.retry_delay)
            try:
                payload = self._list()
            except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
                # Never copy transport exceptions/argv (which can contain the
                # server token) into an observation or receipt.
                if isinstance(exc, RuntimeError) and str(exc) in {
                    "Postmark verifier received invalid JSON",
                    "Postmark verifier received malformed response",
                }:
                    return self._failure(str(exc))
                last_reason = "Postmark verification request failed"
                continue

            if not isinstance(payload, dict):
                return self._failure("malformed Postmark message list")

            messages = payload.get("Messages")

            if not isinstance(messages, list):
                return PostmarkObservation(
                    observed=False,
                    message_id=None,
                    subject=None,
                    recipient=None,
                    status=None,
                    reason=(
                        "malformed Postmark message list"
                    ),
                )

            # A truncated page cannot establish exactly one effect. Keep the
            # existing endpoint; fail closed instead of inventing pagination.
            total = payload.get("TotalCount", len(messages))
            if type(total) is not int or total != len(messages) or len(messages) >= 100:
                return self._failure("malformed Postmark message list")

            matches: list[dict[str, Any]] = []

            for item in messages:
                if not isinstance(item, dict) or not isinstance(item.get("Subject"), str):
                    return self._failure("malformed Postmark message list")

                if item.get("Subject") != self.subject:
                    continue

                recipients = item.get("Recipients")

                if "Recipients" in item:
                    if not isinstance(recipients, list) or not all(
                        isinstance(r, str) for r in recipients
                    ):
                        return self._failure("malformed Postmark message list")
                    recipient_match = (
                        self.recipient in recipients
                    )
                elif isinstance(item.get("To"), str):
                    recipient_match = (
                        item.get("To") == self.recipient
                    )
                else:
                    return self._failure("malformed Postmark message list")

                if not recipient_match:
                    continue

                received_at = (
                    item.get("ReceivedAt")
                    or item.get("SentAt")
                )

                if not isinstance(
                    received_at,
                    str,
                ):
                    return self._failure("malformed Postmark message list")

                try:
                    observed_at = self._parse_time(
                        received_at
                    )
                except ValueError:
                    return self._failure("malformed Postmark message list")

                if observed_at < boundary:
                    continue

                # MULTI-001 prohibits live delivery. A matching
                # vendor effect is eligible only when Postmark
                # independently marks it as sandboxed.
                if item.get("Sandboxed") is not True:
                    return PostmarkObservation(
                        observed=False,
                        message_id=item.get("MessageID"),
                        subject=self.subject,
                        recipient=self.recipient,
                        status=item.get("Status"),
                        reason=(
                            "matching vendor-side message "
                            "was not sandboxed"
                        ),
                    )

                if not isinstance(item.get("MessageID"), str) or not item["MessageID"]:
                    return self._failure("malformed Postmark message list")
                matches.append(item)

                if len(matches) > 1:
                    return PostmarkObservation(
                        observed=False,
                        message_id=None,
                        subject=self.subject,
                        recipient=self.recipient,
                        status=None,
                        reason=(
                            "multiple matching vendor-side "
                            "messages observed"
                        ),
                    )

            if len(matches) == 1:
                match = matches[0]
                # Count the entire subject/recipient cohort BEFORE applying
                # the untrusted ID constraint: an ID must never hide a duplicate.
                if (self.expected_message_id is not None
                        and match["MessageID"].lower() != self.expected_message_id):
                    return self._failure("vendor-side MessageID mismatch")

                return PostmarkObservation(
                    observed=True,
                    message_id=match.get(
                        "MessageID"
                    ),
                    subject=self.subject,
                    recipient=self.recipient,
                    status=(
                        match.get("Status")
                        or match.get("Tag")
                    ),
                    reason=(
                        "exactly one current vendor-side "
                        "message observed"
                    ),
                )

        return PostmarkObservation(
            observed=False,
            message_id=None,
            subject=self.subject,
            recipient=self.recipient,
            status=None,
            reason=last_reason,
        )
