FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn pillow httpx python-multipart itsdangerous

COPY app.py imaging.py notify.py ./
COPY static ./static

RUN useradd --system --uid 10001 magnet && mkdir -p /data && chown magnet /data
USER magnet
VOLUME /data
EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=5s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"

CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
