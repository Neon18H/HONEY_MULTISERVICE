FROM python:3.12-slim

RUN useradd -m -u 10003 mailoney
WORKDIR /opt/mailoney

COPY app.py /opt/mailoney/app.py
COPY entrypoint.sh /entrypoint.sh

RUN mkdir -p /data/logs && chown -R mailoney:mailoney /data /opt/mailoney && chmod +x /entrypoint.sh

USER mailoney
EXPOSE 2525
ENTRYPOINT ["/entrypoint.sh"]
