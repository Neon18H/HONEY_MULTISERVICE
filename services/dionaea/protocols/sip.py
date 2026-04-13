"""Minimal SIP emulation for INVITE/OPTIONS scans."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="sip",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="request",
        raw_data=data,
    )

    response = (
        b"SIP/2.0 401 Unauthorized\r\n"
        b"Via: SIP/2.0/TCP honeypot.local\r\n"
        b"Server: Asterisk PBX 16.0\r\n"
        b"Content-Length: 0\r\n\r\n"
    )
    writer.write(response)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
