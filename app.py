"""Small web service used to reproduce a deployment-only route failure."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from urllib.parse import urlsplit


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Each server instance carries its own deployment configuration.
        health_path = self.server.public_base_path + "/api/health"
        if urlsplit(self.path).path == health_path:
            payload = json.dumps({"status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
        else:
            payload = json.dumps({"error": "not found"}).encode("utf-8")
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def validate_base_path(base_path):
    if not isinstance(base_path, str) or (
        base_path and (
            not base_path.startswith("/")
            or base_path.endswith("/")
            or "//" in base_path
            or "?" in base_path
            or "#" in base_path
        )
    ):
        raise ValueError("public_base_path must be empty or an absolute path without a trailing slash")
    return base_path


def serve(port=0, base_path=""):
    base_path = validate_base_path(base_path)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.public_base_path = base_path
    return server


if __name__ == "__main__":
    server = serve(8080, os.environ.get("PUBLIC_BASE_PATH", ""))
    print(f"listening at http://127.0.0.1:8080{server.public_base_path}", flush=True)
    server.serve_forever()
