# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.1
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy requirements first (for caching)
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install -r requirements.txt

# ✅ Copy all project files before switching user
COPY . .

# ✅ Move credentials file before switching user
RUN mkdir -p calendar_service && \
    mv gen-lang-client-0569941520-2b5f6c75848c.json calendar_service/

# ✅ Now switch to non-root user
USER appuser

EXPOSE 5001

CMD gunicorn 'gc_server:app' --bind=0.0.0.0:5001 --timeout 90
