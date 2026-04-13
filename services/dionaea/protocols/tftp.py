"""Minimal TFTP emulation over UDP."""

from __future__ import annotations

from utils.logger import write_event


def handle(data: bytes, addr: tuple[str, int], port: int) -> None:
    src_ip, src_port = str(addr[0]), int(addr[1])
    write_event(
        service="tftp",
        src_ip=src_ip,
        src_port=src_port,
        dst_port=port,
        protocol="udp",
        event_type="datagram",
        raw_data=data,
    )
