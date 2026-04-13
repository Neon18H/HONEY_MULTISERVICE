"""Shared async server helpers for TCP/UDP protocol emulators."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from utils.logger import write_event

MAX_READ = 4096

TCPHandler = Callable[[asyncio.StreamReader, asyncio.StreamWriter, int], Awaitable[None]]


async def start_tcp_service(port: int, handler: TCPHandler) -> None:
    """Start a TCP service and keep it running forever."""

    async def wrapped(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await handler(reader, writer, port)
        except Exception as exc:  # pragma: no cover - defensive guard
            peer = writer.get_extra_info("peername") or ("unknown", 0)
            write_event(
                service="internal",
                src_ip=str(peer[0]),
                src_port=int(peer[1]),
                dst_port=port,
                protocol="tcp",
                event_type=f"handler_error:{exc.__class__.__name__}",
                raw_data=str(exc).encode(),
            )
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(wrapped, host="0.0.0.0", port=port)
    async with server:
        await server.serve_forever()


class UDPService(asyncio.DatagramProtocol):
    """Reusable UDP protocol wrapper with safe error handling."""

    def __init__(self, port: int, datagram_handler: Callable[[bytes, tuple[str, int], int], None]):
        self.port = port
        self.datagram_handler = datagram_handler

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            self.datagram_handler(data, addr, self.port)
        except Exception as exc:  # pragma: no cover - defensive guard
            write_event(
                service="internal",
                src_ip=str(addr[0]),
                src_port=int(addr[1]),
                dst_port=self.port,
                protocol="udp",
                event_type=f"handler_error:{exc.__class__.__name__}",
                raw_data=str(exc).encode(),
            )


async def start_udp_service(port: int, datagram_handler: Callable[[bytes, tuple[str, int], int], None]) -> None:
    """Start a UDP service and keep it running forever."""
    loop = asyncio.get_running_loop()
    transport, _protocol = await loop.create_datagram_endpoint(
        lambda: UDPService(port, datagram_handler),
        local_addr=("0.0.0.0", port),
    )
    try:
        await asyncio.Future()
    finally:
        transport.close()
