FROM python:3.12-slim

RUN useradd -m -u 10002 elasticpot
WORKDIR /opt/elasticpot

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
RUN mkdir -p /data/logs && chown -R elasticpot:elasticpot /data

USER elasticpot
EXPOSE 9200
CMD ["python", "app.py"]
