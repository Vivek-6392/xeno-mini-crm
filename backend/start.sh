#!/bin/sh

python -m app.seed || true

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000