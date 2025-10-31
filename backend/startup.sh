#!/bin/bash
set -e
uv run alembic upgrade head
uv run python prepare.py data
uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000