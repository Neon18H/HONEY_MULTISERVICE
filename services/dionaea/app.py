"""Lightweight dionaea-like honeypot orchestrator.

Runs independent async protocol emulators for research capture only.
"""

from __future__ import annotations

import asyncio

from protocols import ftp, http, mssql, mysql, pptp, rpc, sip, smb, tftp
from utils.logger import write_event
from utils.server import start_tcp_service, start_udp_service

TCP_SERVICES = {
    21: ("ftp", ftp.handle),
    80: ("http", http.handle),
    135: ("rpc", rpc.handle),
    445: ("smb", smb.handle),
    1433: ("mssql", mssql.handle),
    1723: ("pptp", pptp.handle),
    3306: ("mysql", mysql.handle),
    5060: ("sip", sip.handle),
}

UDP_SERVICES = {
    69: ("tftp", tftp.handle),
}


async def main() -> None:
    tasks = []

    for port, (_name, handler) in TCP_SERVICES.items():
        tasks.append(asyncio.create_task(start_tcp_service(port, handler)))

    for port, (_name, handler) in UDP_SERVICES.items():
        tasks.append(asyncio.create_task(start_udp_service(port, handler)))

    write_event(
        service="dionaea",
        src_ip="127.0.0.1",
        src_port=0,
        dst_port=0,
        protocol="system",
        event_type="startup",
    )

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
