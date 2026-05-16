#!/usr/bin/env bash
# Make executable once: chmod +x run_server.sh

set -euo pipefail

SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVER_DIR"

if [[ ! -f "$SERVER_DIR/.venv/bin/activate" ]]; then
  echo "ERROR: Virtual environment not found at server/.venv" >&2
  echo "" >&2
  echo "Run setup first:" >&2
  echo "  chmod +x setup.sh && ./setup.sh" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$SERVER_DIR/.venv/bin/activate"

if [[ -f "$SERVER_DIR/.env" ]]; then
  echo "[run_server] Using server/.env"
else
  echo "[run_server] Warning: server/.env not found. Copy .env.example to .env"
fi

cd "$SERVER_DIR/src"
echo "[run_server] Starting uvicorn at http://127.0.0.1:8000  (API: /api/v1)"
exec uvicorn main:app --reload
