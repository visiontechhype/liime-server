"""Configuration for Liime Server"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration class for Liime Server"""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Database configuration
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATABASE_PATH: Path = BASE_DIR / "liime.db"
    
    # JWT configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # File upload configuration
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    
    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 60
    
    def __post_init__(self):
        """Create upload directory after initialization"""
        self.UPLOAD_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create Config from environment variables"""
        return cls(
            HOST=os.getenv("LIIME_HOST", cls.HOST),
            PORT=int(os.getenv("LIIME_PORT", str(cls.PORT))),
            DEBUG=os.getenv("LIIME_DEBUG", "false").lower() == "true",
            SECRET_KEY=os.getenv("LIIME_SECRET_KEY", cls.SECRET_KEY)
        )


# Module-level config instance
Config = Config()
