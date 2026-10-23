FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

RUN chown -R 10001:10001 /app
USER 10001:10001

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:5000/', timeout=2)"]

CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--threads=4", "--access-logfile=-", "--error-logfile=-", "app:app"]
