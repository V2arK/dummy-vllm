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
    try:
        response = await stub.Completion(
            openai_pb2.CompletionRequest(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                prompt="Summarize why dummy-vllm exists",
                max_tokens=8,
            ),
            timeout=5.0,
        )
    except grpc.aio.AioRpcError as exc:
        print(f"gRPC completion failed: {exc.code().name} - {exc.details()}")
        return

    print("\n=== gRPC completion ===")
    print(f"ID: {response.id}")
    print(f"Model: {response.model}")
    if response.choices:
        choice = response.choices[0]
        print(f"Finish reason: {choice.finish_reason or '(streaming)'}")
        print(f"Text: {choice.text}")
    if response.usage:
        print(
            f"Usage -> prompt: {response.usage.prompt_tokens}, "
            f"completion: {response.usage.completion_tokens}, "
            f"total: {response.usage.total_tokens}"
        )


async def run_chat_stream(stub: openai_pb2_grpc.VLLMServiceStub) -> None:
    print("\n=== gRPC chat stream ===")
    try:
        stream = stub.ChatCompletionStream(
            openai_pb2.ChatCompletionRequest(
                model="Qwen/Qwen2.5-VL-7B-Instruct",
                messages=[
                    openai_pb2.ChatMessage(role="user", content="Give me a short motivational quote"),
                ],
                max_tokens=6,
            ),
            timeout=5.0,
        )
        async for chunk in stream:
            print(chunk)
            if chunk.choices and chunk.choices[0].finish_reason:
                break
    except grpc.aio.AioRpcError as exc:
        print(f"gRPC streaming failed: {exc.code().name} - {exc.details()}")


async def main() -> None:
    async with grpc.aio.insecure_channel("localhost:9000") as channel:
        stub = openai_pb2_grpc.VLLMServiceStub(channel)
        await channel.channel_ready()
        await run_completion(stub)
        await run_chat_stream(stub)


if __name__ == "__main__":
    asyncio.run(main())

