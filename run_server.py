#!/usr/bin/env python3
"""Run Liime Server"""
import uvicorn
from settings import Config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    )
