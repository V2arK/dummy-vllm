#!/usr/bin/env python3
"""Simple gRPC client for the dummy vLLM backend."""

# Standard library imports
from __future__ import annotations

import asyncio
import pathlib
import sys

# Third-party imports
import grpc

# Local/application imports
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.grpc_service.proto import openai_pb2, openai_pb2_grpc


async def run_completion(stub: openai_pb2_grpc.VLLMServiceStub) -> None:
    response = await stub.Completion(
        openai_pb2.CompletionRequest(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            prompt="Summarize why dummy-vllm exists",
            max_tokens=8,
        )
    )
    print("\n=== gRPC completion ===")
    print(response)


async def run_chat_stream(stub: openai_pb2_grpc.VLLMServiceStub) -> None:
    stream = stub.ChatCompletionStream(
        openai_pb2.ChatCompletionRequest(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=[
                openai_pb2.ChatMessage(role="user", content="Give me a short motivational quote"),
            ],
            max_tokens=6,
        )
    )
    print("\n=== gRPC chat stream ===")
    async for chunk in stream:
        print(chunk)
        if chunk.choices and chunk.choices[0].finish_reason == "stop":
            break


async def main() -> None:
    async with grpc.aio.insecure_channel("localhost:9000") as channel:
        stub = openai_pb2_grpc.VLLMServiceStub(channel)
        await channel.channel_ready()
        await run_completion(stub)
        await run_chat_stream(stub)


if __name__ == "__main__":
    asyncio.run(main())

