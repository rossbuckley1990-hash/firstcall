import http.client
import json
import os


def main():
    key = os.environ.get("ACME_API_KEY")
    if not key:
        return {"ok": False, "stage": "authentication", "error_type": "MissingAPIKey", "http_status": None}

    connection = http.client.HTTPConnection("127.0.0.1", 8765, timeout=30)
    status = None
    stage = "request"
    try:
        connection.request(
            "POST",
            "/v1/events",
            body=json.dumps({"name": "FIRSTCALL CF-001 D01"}),
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        status = response.status
        if not 200 <= status < 300:
            return {"ok": False, "stage": "request", "error_type": "HTTPError", "http_status": status}
        stage = "response"
        event = json.loads(response.read())
        if not isinstance(event, dict) or not event.get("id"):
            return {"ok": False, "stage": stage, "error_type": "InvalidEventResponse", "http_status": status}
        return {"ok": True, "stage": "complete"}
    except Exception:
        return {"ok": False, "stage": stage, "error_type": "RequestError" if stage == "request" else "InvalidEventResponse", "http_status": status}
    finally:
        connection.close()


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
