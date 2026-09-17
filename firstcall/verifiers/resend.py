from __future__ import annotations

from dataclasses import dataclass
import json
import time
import urllib.error
import urllib.request


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
    ):
        self.api_key = api_key
        self.subject = subject
        self.recipient = recipient

    def _list(self) -> dict:
        req = urllib.request.Request(
            "https://api.resend.com/emails?limit=100",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "firstcall-verifier/0.2",
            },
        )

        with urllib.request.urlopen(
            req,
            timeout=30,
        ) as response:
            return json.loads(
                response.read().decode("utf-8")
            )

    def verify(
        self,
        *,
        attempts: int = 10,
        delay: float = 2.0,
    ) -> ResendObservation:
        last_reason = "matching vendor-side email not found"

        for _ in range(attempts):
            try:
                payload = self._list()
            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                json.JSONDecodeError,
            ) as exc:
                last_reason = (
                    "verifier API failure: "
                    + type(exc).__name__
                )
                time.sleep(delay)
                continue

            for item in payload.get("data", []):
                if item.get("subject") != self.subject:
                    continue

                recipients = item.get("to") or []

                if isinstance(recipients, str):
                    recipients = [recipients]

                if self.recipient not in recipients:
                    continue

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
