#!/bin/bash
set -e
cd /home/runner/workspace/artifacts/api-server
python3 seed.py || true
exec python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
