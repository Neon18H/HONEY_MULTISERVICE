import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

from flask import Flask, request, Response
from werkzeug.serving import make_server

LOG_DIR = Path(os.getenv("WEBTRAP_LOG_DIR", "/data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
REQ_LOG = LOG_DIR / "requests.jsonl"
ALERT_LOG = LOG_DIR / "alerts.jsonl"

SUSPICIOUS_PATTERNS = [
    r"union\s+select",
    r"/etc/passwd",
    r"\$\{jndi:",
    r"cmd=",
    r"<script",
    r"\.\./\.\./",
    r"wp-admin",
    r"\.env",
]

app = Flask(__name__)


def write_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


@app.route("/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def trap(subpath: str):
    now = datetime.now(timezone.utc).isoformat()
    request_body = request.get_data(as_text=True)
    event = {
        "timestamp": now,
        "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
        "method": request.method,
        "path": f"/{subpath}",
        "query_string": request.query_string.decode("utf-8", errors="ignore"),
        "headers": dict(request.headers),
        "body": request_body[:8000],
    }
    write_jsonl(REQ_LOG, event)

    raw = f"{event['path']} {event['query_string']} {request_body}"
    if any(re.search(pattern, raw, flags=re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS):
        write_jsonl(ALERT_LOG, event)

    return Response("<html><body><h1>Welcome</h1></body></html>", status=200, mimetype="text/html")


class ServerThread(Thread):
    def __init__(self, host: str, port: int, ssl_context=None):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app, ssl_context=ssl_context)

    def run(self):
        self.server.serve_forever()


if __name__ == "__main__":
    host = os.getenv("WEBTRAP_HOST", "0.0.0.0")
    http_port = int(os.getenv("WEBTRAP_HTTP_PORT", "8080"))
    https_port = int(os.getenv("WEBTRAP_HTTPS_PORT", "8443"))

    http_server = ServerThread(host, http_port)
    http_server.start()

    if os.getenv("WEBTRAP_ENABLE_HTTPS", "true").lower() == "true":
        https_server = ServerThread(host, https_port, ssl_context="adhoc")
        https_server.start()

    http_server.join()
