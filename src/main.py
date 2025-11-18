#!/usr/bin/env python3
"""FastAPI entrypoint for the dummy vLLM backend."""

# Standard library imports
from typing import Any, Dict

# Third-party imports
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local/application imports
from src.config import settings
from src.endpoints import chat, completions, models
from src.utils.metrics import metrics_collector


def create_app() -> FastAPI:
    """Instantiate the FastAPI application."""
    app = FastAPI(
        title="Dummy vLLM Backend",
        description="High-throughput mock backend for FIB performance testing.",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(completions.router, prefix="/v1", tags=["completions"])
    app.include_router(chat.router, prefix="/v1", tags=["chat"])
    app.include_router(models.router, prefix="/v1", tags=["models"])

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "healthy"}

    @app.get("/metrics")
    async def metrics() -> Dict[str, Any]:
        snapshot = metrics_collector.snapshot()
        return {
            "total_requests": snapshot.total_requests,
            "requests_by_endpoint": snapshot.requests_by_endpoint,
            "total_tokens_generated": snapshot.total_tokens_generated,
        }

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        access_log=True,
    )

