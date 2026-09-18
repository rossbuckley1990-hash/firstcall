from __future__ import annotations

from dataclasses import dataclass
import json
import time
import subprocess
from datetime import datetime


@dataclass(frozen=True)
class ResendObservation:
    observed: bool
    email_id: str | None
    subject: str | None
    recipient: str | None
    last_event: str | None
    reason: str | None


class ResendVerifier:
    def __init__(
        self,
        *,
        api_key: str,
        subject: str,
        recipient: str = "delivered@resend.dev",
        created_after: str | None = None,
    ):
        self.api_key = api_key
        self.subject = subject
        self.recipient = recipient
        self.created_after = created_after

    def _list(self, *, after: str | None = None) -> dict:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "--fail-with-body",
                "--max-time", "30",
                "-H",
                f"Authorization: Bearer {self.api_key}",
                "-H",
                "Accept: application/json",
                (
                    "https://api.resend.com/emails?limit=100"
                    + (
                        "&after=" + after
                        if after is not None
                        else ""
                    )
                ),
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Resend verifier curl failed: {result.returncode}"
            )

        return json.loads(result.stdout)

    def verify(
        self,
        *,
        attempts: int = 10,
        delay: float = 2.0,
    ) -> ResendObservation:
        last_reason = "matching vendor-side email not found"

        for _ in range(attempts):
            matches = []
            after = None
            seen_cursors = set()
            verifier_failed = False

            while True:
                try:
                    payload = self._list(after=after)
                except (
                    RuntimeError,
                    subprocess.TimeoutExpired,
                    json.JSONDecodeError,
                ) as exc:
                    last_reason = (
                        "verifier API failure: "
                        + type(exc).__name__
                    )
                    verifier_failed = True
                    break

                data = payload.get("data", [])

                if not isinstance(data, list):
                    last_reason = "invalid verifier list response"
                    verifier_failed = True
                    break

                for item in data:
                    if item.get("subject") != self.subject:
                        continue

                    recipients = item.get("to") or []

                    if isinstance(recipients, str):
                        recipients = [recipients]

                    if self.recipient not in recipients:
                        continue

                    if self.created_after is not None:
                        created_at = item.get("created_at")

                        if not created_at:
                            continue

                        try:
                            created = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            )
                            boundary = datetime.fromisoformat(
                                self.created_after.replace("Z", "+00:00")
                            )
                        except ValueError:
                            continue

                        if created < boundary:
                            continue

                    matches.append(item)

                    if len(matches) > 1:
                        return ResendObservation(
                            observed=False,
                            email_id=None,
                            subject=self.subject,
                            recipient=self.recipient,
                            last_event=None,
                            reason=(
                                "multiple matching vendor-side "
                                "emails observed"
                            ),
                        )

                if not payload.get("has_more"):
                    break

                if not data:
                    last_reason = "invalid empty pagination page"
                    verifier_failed = True
                    break

                cursor = data[-1].get("id")

                if not cursor or cursor in seen_cursors:
                    last_reason = "invalid verifier pagination cursor"
                    verifier_failed = True
                    break

                seen_cursors.add(cursor)
                after = cursor

            if verifier_failed:
                time.sleep(delay)
                continue

            if len(matches) == 1:
                item = matches[0]
                return ResendObservation(
                    observed=True,
                    email_id=item.get("id"),
                    subject=item.get("subject"),
                    recipient=self.recipient,
                    last_event=item.get("last_event"),
                    reason=None,
                )

            time.sleep(delay)

        return ResendObservation(
            observed=False,
            email_id=None,
            subject=None,
            recipient=None,
            last_event=None,
            reason=last_reason,
        )
