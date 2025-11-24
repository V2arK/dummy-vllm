#!/usr/bin/env python3
"""Model listing endpoint."""

# Standard library imports
import time
from typing import Any, Dict, List

# Third-party imports
from fastapi import APIRouter

# Local/application imports
from src.config import settings


router = APIRouter()


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """Return the catalog of available models."""
    created = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": settings.default_model_name,
                "object": "model",
                "created": created,
                "owned_by": "dummy-vllm",
                "permission": [],
                "root": settings.default_model_name,
                "parent": None,
            }
        ],
    }
