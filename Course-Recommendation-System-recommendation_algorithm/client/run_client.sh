#!/usr/bin/env bash
# Make executable once: chmod +x run_client.sh

set -euo pipefail

CLIENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$CLIENT_DIR"

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js was not found on PATH." >&2
  exit 1
fi

if [[ ! -d "$CLIENT_DIR/node_modules" ]]; then
  echo "ERROR: node_modules not found." >&2
  echo "" >&2
  echo "Run setup first:" >&2
  echo "  chmod +x setup.sh && ./setup.sh" >&2
  exit 1
fi

echo "[run_client] Starting Vite at http://localhost:5173"
echo "[run_client] Ensure the backend is running: server/run_server.sh"
exec npm run dev
