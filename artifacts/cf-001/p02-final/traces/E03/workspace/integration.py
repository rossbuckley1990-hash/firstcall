import json
import os
import urllib.error
import urllib.request


def main():
    api_key = os.environ.get("ACME_API_KEY")
    if not api_key:
        return {"ok": False, "stage": "authentication", "error_type": "MissingCredential", "http_status": None}

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = urllib.request.Request(
        "http://127.0.0.1:8765/v1/events",
        data=json.dumps({"name": "FIRSTCALL CF-001 E03"}).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    status = None
    try:
        with opener.open(request, timeout=30) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as error:
        return {"ok": False, "stage": "request", "error_type": "HTTPError", "http_status": error.code}
    except Exception:
        return {"ok": False, "stage": "request", "error_type": "TransportError", "http_status": None}

    if not 200 <= status < 300:
        return {"ok": False, "stage": "response", "error_type": "UnexpectedStatus", "http_status": status}
    try:
        event = json.loads(body)
    except (ValueError, UnicodeError):
        return {"ok": False, "stage": "response", "error_type": "InvalidJSON", "http_status": status}
    if not isinstance(event, dict) or not event.get("id"):
        return {"ok": False, "stage": "response", "error_type": "MissingEventID", "http_status": status}
    return {"ok": True, "stage": "complete"}


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
