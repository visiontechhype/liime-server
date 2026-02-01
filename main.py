#!/usr/bin/env python3
"""Liime Messenger Server - FastAPI Application"""
import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from settings import Config
from models import Base

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = f"sqlite+aiosqlite:///{Config.DATABASE_PATH}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Liime Server...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")
    logger.info(f"Server started at http://{Config.HOST}:{Config.PORT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Liime Server...")
    await engine.dispose()

# Create FastAPI app
app = FastAPI(
    title="Liime Messenger API",
    description="API for Liime Messenger - A Telegram Clone",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from main_router import router as api_router
from auth_router import router as auth_router
from chats import router as chats_router
from messages import router as messages_router
from users import router as users_router
from ws_handler import router as ws_router

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(chats_router, prefix="/api/chats", tags=["Chats"])
app.include_router(messages_router, prefix="/api/messages", tags=["Messages"])
app.include_router(api_router)
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {
        "name": "Liime Messenger Server",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
