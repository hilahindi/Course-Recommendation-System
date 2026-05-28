#!/usr/bin/env bash
# Make executable once: chmod +x setup.sh

set -euo pipefail

CLIENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CLIENT_DIR"

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js was not found on PATH. Install Node.js 18+ and try again." >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm was not found on PATH." >&2
  exit 1
fi

if [[ ! -f "$CLIENT_DIR/package.json" ]]; then
  echo "ERROR: package.json not found in $CLIENT_DIR" >&2
  exit 1
fi

echo "Installing npm dependencies..."
npm install

echo ""
echo "Setup complete. Run: ./run_client.sh"
