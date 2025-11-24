#!/usr/bin/env python3
"""Dummy text generator that returns pre-defined responses instantly."""

# Standard library imports
import asyncio
import random
from typing import AsyncGenerator, List, Tuple

# Local/application imports
from src.config import settings


class DummyTextGenerator:
    """Generate deterministic text fragments for completions."""

    RESPONSE_POOL = [
        "This dummy backend replies instantly to isolate network overhead.",
        "Synthetic completion text for high-concurrency performance testing.",
        "Use this response to validate streaming behavior without GPU latency.",
        "Deterministic filler message generated without any inference cost.",
        "Mock vLLM output enabling benchmarking of pure HTTP throughput.",
    ]

    @staticmethod
    def estimate_token_count(text: str) -> int:
        """Estimate token count using whitespace tokens with a character fallback."""
        tokens, _ = DummyTextGenerator._tokenize_text(text)
        return len(tokens)

    @classmethod
    def generate_completion_with_metadata(cls, max_tokens: int) -> Tuple[str, bool]:
        """Return completion text plus whether it was truncated by max_tokens."""
        tokens, join_with_space, truncated = cls._prepare_tokens(max_tokens=max_tokens)
        if join_with_space:
            text = " ".join(tokens)
        else:
            text = "".join(tokens)
        return text, truncated

    @classmethod
    def generate_completion_text(cls, max_tokens: int) -> str:
        """Return a deterministic completion string clipped to max_tokens."""
        text, _ = cls.generate_completion_with_metadata(max_tokens=max_tokens)
        return text

    @classmethod
    async def stream_tokens(cls, max_tokens: int) -> AsyncGenerator[str, None]:
        """Yield tokens asynchronously with optional artificial delay."""
        tokens, _, _ = cls._prepare_tokens(max_tokens=max_tokens)
        async for token in cls.stream_from_tokens(tokens):
            yield token

    @classmethod
    def prepare_token_stream(cls, max_tokens: int) -> Tuple[List[str], bool]:
        """Prepare tokens for streaming plus truncated flag."""
        tokens, _, truncated = cls._prepare_tokens(max_tokens=max_tokens)
        return tokens, truncated

    @classmethod
    async def stream_from_tokens(cls, tokens: List[str]) -> AsyncGenerator[str, None]:
        await cls._maybe_sleep(settings.ttft_delay_seconds)
        for token in tokens:
            yield token
            await cls._maybe_sleep(cls._token_delay_with_jitter())

    @classmethod
    def _prepare_tokens(cls, max_tokens: int) -> Tuple[List[str], bool, bool]:
        """Prepare a bounded list of tokens plus join style flag."""
        base_response = random.choice(cls.RESPONSE_POOL)
        tokens, join_with_space = cls._tokenize_text(base_response)
        safe_max = max(1, max_tokens)
        truncated = len(tokens) > safe_max
        return tokens[:safe_max], join_with_space, truncated

    @staticmethod
    def _tokenize_text(text: str) -> Tuple[List[str], bool]:
        """Split text into tokens and indicate whether spaces separate them."""
        if not text:
            return [], True
        tokens = text.split()
        if tokens:
            return tokens, True
        return list(text), False

    @staticmethod
    async def _maybe_sleep(delay_seconds: float) -> None:
        """Sleep for the requested time when delay is positive."""
        if delay_seconds <= 0.0:
            return
        await asyncio.sleep(delay_seconds)

    @staticmethod
    def _token_delay_with_jitter() -> float:
        """Return token delay plus jitter bounds."""
        base_delay = settings.token_delay_seconds
        if base_delay <= 0.0:
            return 0.0
        jitter = random.uniform(
            -settings.token_delay_jitter_seconds, settings.token_delay_jitter_seconds
        )
        return max(0.0, base_delay + jitter)
