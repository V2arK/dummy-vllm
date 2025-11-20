#!/usr/bin/env python3
"""Integration tests for the gRPC compatibility layer."""

# Standard library imports
from __future__ import annotations

# Third-party imports
import grpc
import pytest
import pytest_asyncio

# Local/application imports
from src.config import settings
from src.grpc_service.proto import openai_pb2, openai_pb2_grpc
from src.grpc_service.server import build_grpc_server


@pytest_asyncio.fixture
async def grpc_stub() -> openai_pb2_grpc.VLLMServiceStub:
    server, port = build_grpc_server(host="127.0.0.1", port=0)
    await server.start()
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
            await channel.channel_ready()
            stub = openai_pb2_grpc.VLLMServiceStub(channel)
            yield stub
    finally:
        await server.stop(None)


@pytest.mark.asyncio
async def test_grpc_completion_roundtrip(grpc_stub: openai_pb2_grpc.VLLMServiceStub) -> None:
    response = await grpc_stub.Completion(
        openai_pb2.CompletionRequest(
            model=settings.default_model_name,
            prompt="hello world",
            max_tokens=4,
        )
    )
    assert response.model == settings.default_model_name
    assert len(response.choices) >= 1
    assert response.choices[0].finish_reason in ("stop", "")


@pytest.mark.asyncio
async def test_grpc_chat_stream(grpc_stub: openai_pb2_grpc.VLLMServiceStub) -> None:
    stream = grpc_stub.ChatCompletionStream(
        openai_pb2.ChatCompletionRequest(
            model=settings.default_model_name,
            messages=[
                openai_pb2.ChatMessage(role="user", content="say hi"),
            ],
            max_tokens=3,
        )
    )
    chunks = []
    async for chunk in stream:
        chunks.append(chunk)
        # Stop once the completion reports finish_reason.
        if chunk.choices and chunk.choices[0].finish_reason == "stop":
            break
        if len(chunks) > 10:
            break
    assert chunks, "stream yielded no chunks"

