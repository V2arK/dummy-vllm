#!/usr/bin/env python3
"""Helper utilities to translate between proto messages and Pydantic models."""

# Standard library imports
from __future__ import annotations

import time
from typing import Any, Dict, Optional

# Third-party imports

# Local/application imports
from src.grpc_service.proto import openai_pb2
from src.models import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    CompletionUsage,
)


def chat_request_from_proto(
    grpc_request: openai_pb2.ChatCompletionRequest,
    *,
    default_model: str,
    force_stream: Optional[bool] = None,
) -> ChatCompletionRequest:
    """Translate a ChatCompletionRequest proto into our Pydantic model."""
    payload: Dict[str, Any] = {
        "model": grpc_request.model or default_model,
        "messages": [
            ChatCompletionMessage(
                role=message.role or "user", content=message.content or ""
            )
            for message in grpc_request.messages
        ],
    }

    if grpc_request.HasField("max_tokens"):
        payload["max_tokens"] = grpc_request.max_tokens
    if grpc_request.HasField("temperature"):
        payload["temperature"] = grpc_request.temperature
    if grpc_request.HasField("top_p"):
        payload["top_p"] = grpc_request.top_p
    if grpc_request.HasField("n"):
        payload["n"] = grpc_request.n

    if grpc_request.stop:
        payload["stop"] = list(grpc_request.stop)

    stream_value = force_stream
    if stream_value is None and grpc_request.HasField("stream"):
        stream_value = grpc_request.stream
    if stream_value is not None:
        payload["stream"] = stream_value

    return ChatCompletionRequest.model_validate(payload)


def completion_request_from_proto(
    grpc_request: openai_pb2.CompletionRequest,
    *,
    default_model: str,
    force_stream: Optional[bool] = None,
) -> CompletionRequest:
    """Translate a CompletionRequest proto into our Pydantic model."""
    payload: Dict[str, Any] = {"model": grpc_request.model or default_model}

    if grpc_request.HasField("prompt"):
        payload["prompt"] = grpc_request.prompt
    elif grpc_request.HasField("prompts"):
        payload["prompt"] = list(grpc_request.prompts.values)

    if grpc_request.HasField("max_tokens"):
        payload["max_tokens"] = grpc_request.max_tokens
    if grpc_request.HasField("temperature"):
        payload["temperature"] = grpc_request.temperature
    if grpc_request.HasField("top_p"):
        payload["top_p"] = grpc_request.top_p
    if grpc_request.HasField("n"):
        payload["n"] = grpc_request.n

    if grpc_request.stop:
        payload["stop"] = list(grpc_request.stop)

    stream_value = force_stream
    if stream_value is None and grpc_request.HasField("stream"):
        stream_value = grpc_request.stream
    if stream_value is not None:
        payload["stream"] = stream_value

    return CompletionRequest.model_validate(payload)


def completion_response_to_proto(
    response: CompletionResponse,
) -> openai_pb2.CompletionResponse:
    proto = openai_pb2.CompletionResponse(
        id=response.id,
        object=response.object,
        created=int(response.created),
        model=response.model,
    )
    if response.usage is not None:
        _populate_usage(proto.usage, response.usage)
    for choice in response.choices:
        pb_choice = proto.choices.add()
        pb_choice.index = choice.index
        pb_choice.text = choice.text
        if choice.finish_reason is not None:
            pb_choice.finish_reason = choice.finish_reason
    return proto


def chat_response_to_proto(
    response: ChatCompletionResponse,
) -> openai_pb2.ChatCompletionResponse:
    proto = openai_pb2.ChatCompletionResponse(
        id=response.id,
        object=response.object,
        created=int(response.created),
        model=response.model,
    )
    if response.usage is not None:
        _populate_usage(proto.usage, response.usage)
    for choice in response.choices:
        pb_choice = proto.choices.add()
        pb_choice.index = choice.index
        pb_choice.message.role = choice.message.role
        pb_choice.message.content = choice.message.content
        if choice.finish_reason is not None:
            pb_choice.finish_reason = choice.finish_reason
    return proto


def completion_chunk_from_choice(
    *,
    completion_id: str,
    model: str,
    choice_index: int,
    text: str,
    finish_reason: Optional[str],
    completion_tokens: Optional[int] = None,
) -> openai_pb2.CompletionChunk:
    chunk = openai_pb2.CompletionChunk(
        id=completion_id,
        object="text_completion",
        created=int(time.time()),
        model=model,
    )
    choice = chunk.choices.add()
    choice.index = choice_index
    choice.text = text
    if finish_reason is not None:
        choice.finish_reason = finish_reason
    if completion_tokens is not None:
        # Only send completion_tokens, not prompt_tokens.
        # The benchmark uses its own tokenizer for prompt_len, which is more accurate
        # than our simple whitespace-based tokenization.
        chunk.usage.completion_tokens = completion_tokens
        chunk.usage.total_tokens = completion_tokens
    return chunk


def chat_chunk_from_delta(
    *,
    completion_id: str,
    model: str,
    choice_index: int,
    content: str,
    finish_reason: Optional[str],
    completion_tokens: Optional[int] = None,
) -> openai_pb2.ChatCompletionChunk:
    chunk = openai_pb2.ChatCompletionChunk(
        id=completion_id,
        object="chat.completion.chunk",
        created=int(time.time()),
        model=model,
    )
    choice = chunk.choices.add()
    choice.index = choice_index
    choice.delta.content = content
    if finish_reason is not None:
        choice.finish_reason = finish_reason
    if completion_tokens is not None:
        # Only send completion_tokens, not prompt_tokens.
        # The benchmark uses its own tokenizer for prompt_len, which is more accurate
        # than our simple whitespace-based tokenization.
        chunk.usage.completion_tokens = completion_tokens
        chunk.usage.total_tokens = completion_tokens
    return chunk


def _populate_usage(proto_usage: openai_pb2.Usage, usage: CompletionUsage) -> None:
    proto_usage.prompt_tokens = usage.prompt_tokens
    proto_usage.completion_tokens = usage.completion_tokens
    proto_usage.total_tokens = usage.total_tokens
