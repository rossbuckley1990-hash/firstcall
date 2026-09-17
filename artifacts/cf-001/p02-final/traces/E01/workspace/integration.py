import json
import os
import urllib.error
import urllib.request


def main():
    key = os.environ.get("ACME_API_KEY")
    if not key:
        return {"ok": False, "stage": "authentication", "error_type": "MissingCredential", "http_status": None}

    request = urllib.request.Request(
        "http://127.0.0.1:8765/v1/events",
        data=json.dumps({"name": "FIRSTCALL CF-001 E01"}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    # Disable redirects to ensure a single product request, without retries.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect())
    status = None
    try:
        with opener.open(request, timeout=30) as response:
            status = response.status
            payload = response.read()
    except urllib.error.HTTPError as exc:
        return {"ok": False, "stage": "create_event", "error_type": "HTTPError", "http_status": exc.code}
    except Exception:
        return {"ok": False, "stage": "create_event", "error_type": "TransportError", "http_status": None}

    try:
        event = json.loads(payload)
        if not isinstance(event, dict) or not event.get("id"):
            raise ValueError()
    except Exception:
        return {"ok": False, "stage": "validate_response", "error_type": "InvalidEventResponse", "http_status": status}
    return {"ok": True, "stage": "complete"}


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
