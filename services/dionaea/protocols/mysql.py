"""Minimal MySQL handshake emulation."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

HANDSHAKE = (
    b"\x4a\x00\x00\x00\x0a5.7.36\x00"
    + b"\x2a\x00\x00\x00"
    + b"abcdefgh\x00"
    + b"\xff\xf7"
    + b"\x21"
    + b"\x02\x00"
    + b"\x0f\x80"
    + b"\x15"
    + (b"\x00" * 10)
    + b"ijklmnopqrst\x00"
    + b"mysql_native_password\x00"
)


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    write_event(service="mysql", src_ip=src_ip, src_port=src_port, dst_port=port, protocol="tcp", event_type="connect")

    writer.write(HANDSHAKE)
    await writer.drain()

    data = await reader.read(MAX_READ)
    write_event(
        service="mysql",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="auth_attempt",
        raw_data=data,
    )

    writer.close()
    await writer.wait_closed()
