"""Minimal PPTP emulation with Start-Control-Connection-Reply."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

SCCR = bytes.fromhex(
    "001c000100010000000000010000000000000000"
    "000000000000000000000000"
)


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="pptp",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="start_control_connection",
        raw_data=data,
    )

    writer.write(SCCR)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
