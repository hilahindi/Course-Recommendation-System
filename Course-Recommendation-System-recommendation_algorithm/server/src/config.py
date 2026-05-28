"""Application configuration and environment loading."""

from pathlib import Path

from dotenv import load_dotenv

# server/ directory (parent of src/)
SERVER_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(SERVER_ROOT / ".env")
