"""Minimal RPC Endpoint Mapper emulation."""

from __future__ import annotations

from utils.logger import write_event
from utils.server import MAX_READ

RPC_BIND_ACK = bytes.fromhex("05000c031000000000000000")


async def handle(reader, writer, port: int) -> None:
    peer = writer.get_extra_info("peername") or ("unknown", 0)
    src_ip, src_port = str(peer[0]), int(peer[1])
    data = await reader.read(MAX_READ)

    write_event(
        service="rpc",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="tcp",
        event_type="rpc_bind_attempt",
        raw_data=data,
    )

    writer.write(RPC_BIND_ACK)
    await writer.drain()
    writer.close()
    await writer.wait_closed()
