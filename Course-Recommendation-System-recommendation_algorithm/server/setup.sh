#!/usr/bin/env bash
# Make executable once: chmod +x setup.sh

set -euo pipefail

SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVER_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found on PATH. Install Python 3.8+ and try again." >&2
  exit 1
fi

if [[ ! -f "$SERVER_DIR/requirements.txt" ]]; then
  echo "ERROR: requirements.txt not found in $SERVER_DIR" >&2
  exit 1
fi

if [[ ! -f "$SERVER_DIR/.venv/bin/python" ]]; then
  echo "Creating server/.venv ..."
  python3 -m venv .venv
else
  echo "server/.venv already exists."
fi

# shellcheck source=/dev/null
source "$SERVER_DIR/.venv/bin/activate"

echo "Upgrading pip ..."
python -m pip install --upgrade pip

echo "Installing dependencies from requirements.txt ..."
python -m pip install -r requirements.txt

echo ""
echo "Setup complete."
echo "  1. Copy .env.example to .env and set your API keys"
echo "  2. Seed DB: ./seed.sh"
echo "  3. Run: ./run_server.sh"
