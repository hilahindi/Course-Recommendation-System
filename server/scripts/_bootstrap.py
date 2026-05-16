"""
Shared setup for database seed scripts.

- Loads server/.env before any database imports
- Adds server/src to sys.path so `database`, `models`, and `config` resolve
- Exposes SERVER_ROOT and PROJECT_ROOT for data file paths
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

SCRIPTS_DIR = Path(__file__).resolve().parent
SERVER_ROOT = SCRIPTS_DIR.parent
SRC_DIR = SERVER_ROOT / "src"
PROJECT_ROOT = SERVER_ROOT.parent

# Load environment first so DATABASE_URL is set before engine creation
_env_file = SERVER_ROOT / ".env"
if _env_file.is_file():
    load_dotenv(_env_file)
else:
    load_dotenv()  # fallback: cwd or parent search

# Ensure imports work whether the script is run from server/ or server/scripts/
for path in (SRC_DIR, SCRIPTS_DIR):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)
