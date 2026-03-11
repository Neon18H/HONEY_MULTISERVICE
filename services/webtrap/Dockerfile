FROM python:3.12-slim

RUN useradd -m -u 10001 webtrap
WORKDIR /opt/webtrap

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
RUN mkdir -p /data/logs && chown -R webtrap:webtrap /data

USER webtrap
EXPOSE 8080 8443
CMD ["python", "app.py"]
