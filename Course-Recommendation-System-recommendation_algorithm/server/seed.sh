#!/usr/bin/env bash
# Make executable once: chmod +x seed.sh

set -euo pipefail

SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVER_DIR"

if [[ ! -f "$SERVER_DIR/.venv/bin/python" ]]; then
  echo "ERROR: Virtual environment not found. Run ./setup.sh first." >&2
  exit 1
fi

if [[ ! -f "$SERVER_DIR/.env" ]]; then
  echo "ERROR: server/.env not found. Copy .env.example to .env" >&2
  exit 1
fi

echo "[seed] Running scripts/seed.py ..."
exec "$SERVER_DIR/.venv/bin/python" "$SERVER_DIR/scripts/seed.py"
