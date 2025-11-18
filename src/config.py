#!/usr/bin/env python3
"""Server configuration helpers for the dummy vLLM backend."""

# Standard library imports
import os
from dataclasses import dataclass


def _float_from_env(name: str, default: float) -> float:
    """Retrieve a float environment variable with graceful fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _int_from_env(name: str, default: int) -> int:
    """Retrieve an integer environment variable with graceful fallback."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


@dataclass(frozen=True)
class ServerSettings:
    """Configuration values populated from environment variables."""

    host: str = os.getenv("DUMMY_VLLM_HOST", "0.0.0.0")
    port: int = _int_from_env("DUMMY_VLLM_PORT", 8000)
    log_level: str = os.getenv("DUMMY_VLLM_LOG_LEVEL", "info")
    ttft_delay_seconds: float = _float_from_env("DUMMY_VLLM_TTFT_DELAY", 0.0)
    token_delay_seconds: float = _float_from_env("DUMMY_VLLM_TOKEN_DELAY", 0.0)
    token_delay_jitter_seconds: float = _float_from_env("DUMMY_VLLM_TOKEN_DELAY_JITTER", 0.0)
    default_model_name: str = os.getenv("DUMMY_VLLM_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")


settings = ServerSettings()

