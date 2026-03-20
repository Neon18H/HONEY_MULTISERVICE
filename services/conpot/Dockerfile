FROM python:3.12-slim

RUN useradd -m -u 10004 conpot
WORKDIR /opt/conpot

COPY app.py /opt/conpot/app.py
COPY entrypoint.sh /entrypoint.sh

RUN mkdir -p /data/logs /data/configs && chown -R conpot:conpot /data /opt/conpot && chmod +x /entrypoint.sh

USER conpot
EXPOSE 1102 1502 16100/udp 44818
ENTRYPOINT ["/entrypoint.sh"]
