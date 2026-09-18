from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import subprocess
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
    at or after the current FIRSTCALL run boundary.
    """

    def __init__(
        self,
        *,
        server_token: str,
        subject: str,
        recipient: str,
        created_after: str,
        attempts: int = 3,
    ) -> None:
        self.server_token = server_token
        self.subject = subject
        self.recipient = recipient
        self.created_after = created_after
        self.attempts = attempts

    @staticmethod
    def _parse_time(value: str) -> datetime:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    def _list(self) -> dict[str, Any]:
        completed = subprocess.run(
            [
                "curl",
                "-sS",
                "--fail-with-body",
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

    def verify(self) -> PostmarkObservation:
        boundary = self._parse_time(
            self.created_after
        )

        last_reason = "vendor effect not observed"

        for _ in range(self.attempts):
            try:
                payload = self._list()
            except RuntimeError as exc:
                last_reason = str(exc)
                continue

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

            matches: list[dict[str, Any]] = []

            for item in messages:
                if not isinstance(item, dict):
                    continue

                if item.get("Subject") != self.subject:
                    continue

                recipients = item.get("Recipients")

                if isinstance(recipients, list):
                    recipient_match = (
                        self.recipient in recipients
                    )
                else:
                    recipient_match = (
                        item.get("To") == self.recipient
                    )

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
                    continue

                try:
                    observed_at = self._parse_time(
                        received_at
                    )
                except ValueError:
                    continue

                if observed_at < boundary:
                    continue

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
