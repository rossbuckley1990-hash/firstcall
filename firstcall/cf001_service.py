from __future__ import annotations
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = "FIRSTCALL_LOCAL_TOKEN"
VERIFY_TOKEN = "FIRSTCALL_VERIFIER_ONLY"
EVENTS = {}
LOCK = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/v1/events":
            self.send_json(404, {"error": "not_found"})
            return

        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_json(401, {"error": "unauthorized"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
        except Exception:
            self.send_json(400, {"error": "invalid_json"})
            return

        name = payload.get("name")
        if not isinstance(name, str) or not name:
            self.send_json(400, {"error": "missing_name"})
            return

        event_id = "evt_" + uuid.uuid4().hex

        event = {
            "id": event_id,
            "name": name,
        }

        with LOCK:
            EVENTS[event_id] = event

        self.send_json(201, event)

    def do_GET(self):
        if self.headers.get("X-Firstcall-Verifier") != VERIFY_TOKEN:
            self.send_json(403, {"error": "forbidden"})
            return

        if self.path.startswith("/_firstcall/verify/events/"):
            event_id = self.path.rsplit("/", 1)[-1]

            with LOCK:
                event = EVENTS.get(event_id)

            if event is None:
                self.send_json(404, {"error": "not_found"})
                return

            self.send_json(200, event)
            return

        if self.path.startswith("/_firstcall/verify-count?"):
            from urllib.parse import parse_qs, urlparse

            query = parse_qs(urlparse(self.path).query)
            name = query.get("name", [None])[0]

            with LOCK:
                matches = [
                    event
                    for event in EVENTS.values()
                    if event.get("name") == name
                ]

            self.send_json(
                200,
                {
                    "name": name,
                    "count": len(matches),
                    "event_ids": [
                        event["id"]
                        for event in matches
                    ],
                },
            )
            return

        self.send_json(404, {"error": "not_found"})

def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("CF-001 SERVICE READY", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()
