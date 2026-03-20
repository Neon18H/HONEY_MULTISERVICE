import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, request

LOG_DIR = Path(os.getenv("ELASTICPOT_LOG_DIR", "/data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
REQ_LOG = LOG_DIR / "elasticpot.jsonl"

app = Flask(__name__)


def write_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


@app.route("/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"])
@app.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "HEAD", "PATCH"])
def trap(subpath: str):
    now = datetime.now(timezone.utc).isoformat()
    payload = request.get_data(as_text=True)

    event = {
        "timestamp": now,
        "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
        "method": request.method,
        "path": f"/{subpath}",
        "query_string": request.query_string.decode("utf-8", errors="ignore"),
        "headers": dict(request.headers),
        "body": payload[:8000],
    }
    write_jsonl(REQ_LOG, event)

    body = {
        "name": "elasticpot",
        "cluster_name": "elasticsearch",
        "cluster_uuid": "_na_",
        "version": {
            "number": "7.10.2",
            "build_flavor": "default",
            "build_type": "docker",
            "lucene_version": "8.7.0",
        },
        "tagline": "You Know, for Search",
    }
    return Response(json.dumps(body), status=200, mimetype="application/json")


if __name__ == "__main__":
    port = int(os.getenv("ELASTICPOT_PORT", "9200"))
    app.run(host="0.0.0.0", port=port)
