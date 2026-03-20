import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(os.getenv("CONPOT_LOG_DIR", "/data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "ics_events.jsonl"

PORT_S7 = int(os.getenv("CONPOT_S7_PORT", "1102"))
PORT_MODBUS = int(os.getenv("CONPOT_MODBUS_PORT", "1502"))
PORT_ENIP = int(os.getenv("CONPOT_ENIP_PORT", "44818"))
PORT_SNMP = int(os.getenv("CONPOT_SNMP_PORT", "16100"))
MAX_BYTES = 8192


PROFILES = {
    PORT_S7: (b"\x03\x00\x00\x16\x11\xe0\x00\x00\x00\x01\x00\xc1\x02\x01\x00\xc2\x02\x01\x02", "s7comm"),
    PORT_MODBUS: (b"\x00\x01\x00\x00\x00\x03\x01\x83\x02", "modbus"),
    PORT_ENIP: (b"\x65\x00\x04\x00\x01\x00\x00\x00", "enip"),
}


def write_event(event: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


async def handle_tcp(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, label: str, listen_port: int, response: bytes) -> None:
    peer = writer.get_extra_info("peername")
    ip = peer[0] if peer else "unknown"
    remote_port = peer[1] if peer else 0

    data = await reader.read(MAX_BYTES)
    write_event(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transport": "tcp",
            "service": label,
            "listen_port": listen_port,
            "remote_addr": ip,
            "remote_port": remote_port,
            "bytes_in": len(data),
            "payload_hex": data.hex()[:4000],
        }
    )

    if response:
        writer.write(response)
        await writer.drain()
    writer.close()
    await writer.wait_closed()


async def run_tcp_server(listen_port: int, response: bytes, label: str) -> None:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        await handle_tcp(reader, writer, label, listen_port, response)

    server = await asyncio.start_server(handler, host="0.0.0.0", port=listen_port)
    async with server:
        await server.serve_forever()


class HoneyUDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, addr):
        ip, remote_port = addr
        write_event(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "transport": "udp",
                "service": "snmp-lite",
                "listen_port": PORT_SNMP,
                "remote_addr": ip,
                "remote_port": remote_port,
                "bytes_in": len(data),
                "payload_hex": data.hex()[:4000],
            }
        )


async def run_udp_server() -> None:
    loop = asyncio.get_running_loop()
    transport, _protocol = await loop.create_datagram_endpoint(
        HoneyUDPProtocol,
        local_addr=("0.0.0.0", PORT_SNMP),
    )
    try:
        await asyncio.Future()
    finally:
        transport.close()


async def main() -> None:
    tasks = [run_udp_server()]
    for port, (response, label) in PROFILES.items():
        tasks.append(run_tcp_server(port, response, label))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
