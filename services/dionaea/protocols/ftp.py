"""Minimal FTP emulation (banner + USER/PASS prompts)."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])

    write_event(service="ftp", src_ip=src_ip, src_port=src_port, dst_port=port, protocol="tcp", event_type="connect")
    writer.write(b"220 (vsFTPd 3.0.3)\r\n")
    await writer.drain()

    data = await reader.read(MAX_READ)
    write_event(
        service="ftp",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="initial_payload",
        raw_data=data,
    )

    if data:
        writer.write(b"331 Please specify the password.\r\n")
        await writer.drain()

    writer.write(b"530 Login incorrect.\r\n")
    await writer.drain()
    writer.close()
    await writer.wait_closed()
