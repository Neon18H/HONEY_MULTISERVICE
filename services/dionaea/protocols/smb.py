"""Minimal SMB emulation returning a generic negotiation-like reply."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

SMB_REPLY = bytes.fromhex("00000031ff534d4272000000008801c000000000000000000000000000000000000000000011000300010000000000")


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="smb",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="negotiate",
        raw_data=data,
    )

    writer.write(SMB_REPLY)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
