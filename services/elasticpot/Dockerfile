FROM python:3.12-slim

RUN useradd -m -u 10002 elasticpot
WORKDIR /opt/elasticpot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && mkdir -p /data/logs

EXPOSE 9200
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "app.py"]
