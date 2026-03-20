import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("MAILONEY_LOG_DIR", "/data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "smtp_events.jsonl"
BANNER_HOST = os.getenv("MAILONEY_BANNER_HOST", "mail.local")
LISTEN_PORT = int(os.getenv("MAILONEY_PORT", "2525"))
MAX_LINE = 4096


def write_event(event: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    ip = peer[0] if peer else "unknown"
    port = peer[1] if peer else 0

    session = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "connect",
        "remote_addr": ip,
        "remote_port": port,
    }
    write_event(session)

    writer.write(f"220 {BANNER_HOST} ESMTP Mailoney\r\n".encode())
    await writer.drain()

    mail_from = ""
    recipients = []

    while not reader.at_eof():
        raw = await reader.readline()
        if not raw:
            break

        line = raw.decode(errors="ignore").strip()[:MAX_LINE]
        upper = line.upper()

        write_event(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "command",
                "remote_addr": ip,
                "remote_port": port,
                "command": line,
            }
        )

        if upper.startswith(("EHLO", "HELO")):
            writer.write(f"250-{BANNER_HOST} greets you\r\n250 AUTH PLAIN LOGIN\r\n".encode())
        elif upper.startswith("MAIL FROM:"):
            mail_from = line[10:].strip()
            writer.write(b"250 2.1.0 Ok\r\n")
        elif upper.startswith("RCPT TO:"):
            recipients.append(line[8:].strip())
            writer.write(b"250 2.1.5 Ok\r\n")
        elif upper == "DATA":
            writer.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
            await writer.drain()
            data_lines = []
            while True:
                data_raw = await reader.readline()
                if not data_raw:
                    break
                chunk = data_raw.decode(errors="ignore")
                if chunk.strip() == ".":
                    break
                data_lines.append(chunk.rstrip("\r\n"))

            write_event(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "message",
                    "remote_addr": ip,
                    "remote_port": port,
                    "mail_from": mail_from,
                    "rcpt_to": recipients,
                    "data": "\n".join(data_lines)[:16000],
                }
            )
            writer.write(b"250 2.0.0 queued as 1337\r\n")
        elif upper == "RSET":
            mail_from = ""
            recipients = []
            writer.write(b"250 2.0.0 Reset state\r\n")
        elif upper == "NOOP":
            writer.write(b"250 2.0.0 Ok\r\n")
        elif upper == "QUIT":
            writer.write(b"221 2.0.0 Bye\r\n")
            await writer.drain()
            break
        else:
            writer.write(b"250 2.0.0 Ok\r\n")

        await writer.drain()

    write_event(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "disconnect",
            "remote_addr": ip,
            "remote_port": port,
        }
    )
    writer.close()
    await writer.wait_closed()


async def main() -> None:
    server = await asyncio.start_server(handle_client, host="0.0.0.0", port=LISTEN_PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
