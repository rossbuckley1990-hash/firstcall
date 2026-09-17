import json
import os
import urllib.error
import urllib.request


def main():
    key = os.environ.get("ACME_API_KEY")
    if not key:
        return {"ok": False, "stage": "authentication", "error_type": "missing_api_key", "http_status": None}

    request = urllib.request.Request(
        "http://127.0.0.1:8765/v1/events",
        data=json.dumps({"name": "FIRSTCALL CF-001 D02"}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )

    # Do not follow redirects or retry: submit exactly one creation request.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=30) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as exc:
        return {"ok": False, "stage": "create_event", "error_type": "http_error", "http_status": exc.code}
    except Exception:
        return {"ok": False, "stage": "create_event", "error_type": "request_error", "http_status": None}

    if not 200 <= status < 300:
        return {"ok": False, "stage": "create_event", "error_type": "unexpected_status", "http_status": status}
    try:
        event = json.loads(body)
    except (ValueError, UnicodeError):
        return {"ok": False, "stage": "validate_response", "error_type": "invalid_json", "http_status": status}
    if not isinstance(event, dict) or not event.get("id"):
        return {"ok": False, "stage": "validate_response", "error_type": "missing_event_id", "http_status": status}
    return {"ok": True, "stage": "complete"}


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
