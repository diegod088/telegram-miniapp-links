#!/bin/bash
source venv/bin/activate
export PYTHONPATH=.

echo "Iniciando El nuevo servidor TGLinktree FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
