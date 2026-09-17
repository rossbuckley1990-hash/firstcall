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
        data=json.dumps({"name": "FIRSTCALL CF-001 E02"}).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    # Disable redirects so the single product request cannot be replayed.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    status = None
    try:
        with opener.open(request, timeout=30) as response:
            status = response.status
            event = json.load(response)
        if not isinstance(event, dict) or not event.get("id"):
            return {"ok": False, "stage": "response", "error_type": "InvalidEventResponse", "http_status": status}
        return {"ok": True, "stage": "complete"}
    except urllib.error.HTTPError as error:
        return {"ok": False, "stage": "request", "error_type": "HTTPError", "http_status": error.code}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"ok": False, "stage": "request", "error_type": "TransportError", "http_status": status}
    except (ValueError, UnicodeError):
        return {"ok": False, "stage": "response", "error_type": "InvalidJSON", "http_status": status}


if __name__ == "__main__":
    print("FIRSTCALL_RESULT " + json.dumps(main(), separators=(",", ":")))
