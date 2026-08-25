FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN addgroup --system intake && adduser --system --ingroup intake intake

COPY pyproject.toml README.md ./
COPY app ./app
COPY prompts ./prompts
COPY samples ./samples

RUN python -m pip install --upgrade pip && \
    python -m pip install . && \
    mkdir -p /app/outputs && \
    chown -R intake:intake /app

USER intake

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health', timeout=3)"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
