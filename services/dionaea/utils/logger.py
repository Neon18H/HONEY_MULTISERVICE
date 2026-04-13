"""JSONL logger utilities for the lightweight dionaea-like honeypot."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

LOG_DIR = Path(os.getenv("DIONAEA_LOG_DIR", "/app/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "events.jsonl"
_MAX_PREVIEW = int(os.getenv("DIONAEA_MAX_PREVIEW", "1024"))
_lock = Lock()


def _to_preview(data: bytes) -> str:
    """Build a safe payload preview for logs."""
    if not data:
        return ""
    text = data[:_MAX_PREVIEW].decode("utf-8", errors="replace")
    return text.replace("\n", "\\n").replace("\r", "\\r")


def write_event(
    *,
    service: str,
    src_ip: str,
    src_port: int,
    dst_port: int,
    protocol: str,
    event_type: str,
    raw_data: bytes = b"",
) -> None:
    """Write a normalized honeypot event in JSONL format."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "src_ip": src_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": protocol,
        "event_type": event_type,
        "raw_preview": _to_preview(raw_data),
    }

    with _lock:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
