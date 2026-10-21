FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/devlogs-plus/devlogs-plus-backend"
LABEL authors="ArmadilloMike"
LABEL version="2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 60 --forwarded-allow-ips='*' 'app:create_app()'"]