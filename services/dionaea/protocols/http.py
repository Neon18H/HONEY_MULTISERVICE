"""Minimal HTTP emulation with static realistic server response."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

RESPONSE = (
    b"HTTP/1.1 200 OK\r\n"
    b"Server: Apache/2.4.54 (Debian)\r\n"
    b"Content-Type: text/html; charset=utf-8\r\n"
    b"Connection: close\r\n"
    b"Content-Length: 56\r\n\r\n"
    b"<html><body><h1>It works.</h1><p>nginx</p></body></html>"
)


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="http",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="request",
        raw_data=data,
    )

    writer.write(RESPONSE)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
