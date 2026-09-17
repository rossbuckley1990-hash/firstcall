from __future__ import annotations

from dataclasses import dataclass
import json
import time
import urllib.error
import urllib.request


@dataclass(frozen=True)
class Verification:
    observed: bool | None
    email_id: str | None
    last_event: str | None
    reason: str | None


class ResendVerifier:
    def __init__(
        self,
        *,
        api_key: str,
        subject: str,
    ):
        self.api_key = api_key
        self.subject = subject

    def verify(
        self,
        attempts: int = 10,
        delay: float = 2.0,
    ) -> Verification:

        transport_failures = 0

        for _ in range(attempts):
            request = urllib.request.Request(
                "https://api.resend.com/emails?limit=100",
                headers={
                    "Authorization":
                        f"Bearer {self.api_key}",
                    "Accept":
                        "application/json",
                    "User-Agent":
                        "firstcall-verifier/0.4",
                },
            )

            try:
                with urllib.request.urlopen(
                    request,
                    timeout=30,
                ) as response:
                    payload = json.loads(
                        response.read().decode()
                    )

            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                TimeoutError,
                json.JSONDecodeError,
            ):
                transport_failures += 1
                time.sleep(delay)
                continue

            for email in payload.get("data", []):
                if (
                    email.get("subject")
                    != self.subject
                ):
                    continue

                recipients = email.get("to") or []

                if isinstance(
                    recipients,
                    str,
                ):
                    recipients = [recipients]

                if (
                    "delivered@resend.dev"
                    not in recipients
                ):
                    continue

                return Verification(
                    observed=True,
                    email_id=email.get("id"),
                    last_event=email.get(
                        "last_event"
                    ),
                    reason=None,
                )

            time.sleep(delay)

        # If every verifier attempt failed at transport
        # level, the integration result is unknowable.
        if transport_failures == attempts:
            return Verification(
                observed=None,
                email_id=None,
                last_event=None,
                reason=(
                    "independent verifier unavailable"
                ),
            )

        return Verification(
            observed=False,
            email_id=None,
            last_event=None,
            reason=(
                "no matching vendor-side effect"
            ),
        )
