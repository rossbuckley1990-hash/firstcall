"""Create the requested Acme event with one request and no retries."""

import http.client
import json
import os


def main():
    stage = "configuration"
    status = None
    connection = None
    try:
        api_key = os.environ.get("ACME_API_KEY")
        if not api_key:
            return {
                "ok": False,
                "stage": stage,
                "error_type": "MissingAPIKey",
                "http_status": None,
            }

        stage = "request"
        connection = http.client.HTTPConnection("127.0.0.1", 8765, timeout=30)
        connection.request(
            "POST",
            "/v1/events",
            body=json.dumps({"name": "FIRSTCALL CF-001 D03"}).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response = connection.getresponse()
        status = response.status
        if not 200 <= status < 300:
            return {
                "ok": False,
                "stage": stage,
                "error_type": "HTTPError",
                "http_status": status,
            }

        stage = "response"
        event = json.loads(response.read())
        if not isinstance(event, dict) or not event.get("id"):
            return {
                "ok": False,
                "stage": stage,
                "error_type": "InvalidEventResponse",
                "http_status": status,
            }
        return {"ok": True, "stage": "complete"}
    except Exception:
        return {
            "ok": False,
            "stage": stage,
            "error_type": "IntegrationError",
            "http_status": status,
        }
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
