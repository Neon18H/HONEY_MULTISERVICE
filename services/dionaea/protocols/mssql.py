"""Minimal MSSQL emulation with pre-login style payload."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

PRELOGIN_REPLY = bytes.fromhex("040100250000010000001a00060100200001020021000103002200040400260001ff120500010000")


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="mssql",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="prelogin",
        raw_data=data,
    )

    writer.write(PRELOGIN_REPLY)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
