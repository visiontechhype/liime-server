"""Configuration for Liime Server"""
import os
from pathlib import Path

# Server configuration
HOST = os.getenv("LIIME_HOST", "0.0.0.0")
PORT = int(os.getenv("LIIME_PORT", "8000"))
DEBUG = os.getenv("LIIME_DEBUG", "false").lower() == "true"

# Database configuration
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "liime.db"

# JWT configuration
SECRET_KEY = os.getenv("LIIME_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# File upload configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# WebSocket configuration
WS_HEARTBEAT_INTERVAL = 30
WS_PING_TIMEOUT = 60
