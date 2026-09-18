from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess


@dataclass(frozen=True)
class PostmarkPreflight:
    safe: bool
    delivery_type: str | None
    server_id: int | None
    reason: str


def inspect_server(
    server_token: str,
) -> PostmarkPreflight:
    if not server_token:
        return PostmarkPreflight(
            safe=False,
            delivery_type=None,
            server_id=None,
            reason="missing Postmark server token",
        )

    completed = subprocess.run(
        [
            "curl",
            "-sS",
            "--fail-with-body",
            "https://api.postmarkapp.com/server",
            "-H",
            "Accept: application/json",
            "-H",
            (
                "X-Postmark-Server-Token: "
                + server_token
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        return PostmarkPreflight(
            safe=False,
            delivery_type=None,
            server_id=None,
            reason="Postmark server inspection failed",
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return PostmarkPreflight(
            safe=False,
            delivery_type=None,
            server_id=None,
            reason="invalid Postmark server response",
        )

    if not isinstance(payload, dict):
        return PostmarkPreflight(
            safe=False,
            delivery_type=None,
            server_id=None,
            reason="malformed Postmark server response",
        )

    delivery_type = payload.get("DeliveryType")
    server_id = payload.get("ID")

    if delivery_type != "Sandbox":
        return PostmarkPreflight(
            safe=False,
            delivery_type=(
                delivery_type
                if isinstance(delivery_type, str)
                else None
            ),
            server_id=(
                server_id
                if isinstance(server_id, int)
                else None
            ),
            reason=(
                "Postmark server is not Sandbox"
            ),
        )

    return PostmarkPreflight(
        safe=True,
        delivery_type="Sandbox",
        server_id=(
            server_id
            if isinstance(server_id, int)
            else None
        ),
        reason="Postmark Sandbox server confirmed",
    )
