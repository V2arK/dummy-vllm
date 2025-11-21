#!/usr/bin/env python3
"""gRPC service implementation mirroring the OpenAI-compatible API."""

# Standard library imports
from __future__ import annotations

import logging
import time
from typing import AsyncIterator, Iterable, List, Tuple

# Third-party imports
import grpc
from grpc import aio

# Local/application imports
from src.config import settings
from src.generators.dummy_generator import DummyTextGenerator
from src.generators.response_builder import ResponseBuilder
from src.grpc_service import converters
from src.grpc_service.proto import openai_pb2, openai_pb2_grpc
from src.models import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
)
from src.utils.metrics import metrics_collector

logger = logging.getLogger(__name__)


class DummyGrpcServicer(openai_pb2_grpc.VLLMServiceServicer):
    """Implements the gRPC methods backed by the dummy generator."""

    def __init__(self) -> None:
        self._model_name = settings.default_model_name

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    async def ServerLive(
        self,
        request: openai_pb2.ServerLiveRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ServerLiveResponse:
        del request, context
        return openai_pb2.ServerLiveResponse(live=True)

    async def ServerReady(
        self,
        request: openai_pb2.ServerReadyRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ServerReadyResponse:
        del request, context
        return openai_pb2.ServerReadyResponse(ready=True)

    async def ModelReady(
        self,
        request: openai_pb2.ModelReadyRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ModelReadyResponse:
        del context
        name = request.name or self._model_name
        return openai_pb2.ModelReadyResponse(ready=True, name=name)

    # ------------------------------------------------------------------
    # Model metadata
    # ------------------------------------------------------------------

    async def ListModels(
        self,
        request: openai_pb2.ListModelsRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ListModelsResponse:
        del request, context
        response = openai_pb2.ListModelsResponse(object="list")
        info = response.data.add()
        info.id = self._model_name
        info.object = "model"
        info.created = int(time.time())
        info.owned_by = "dummy-vllm"
        info.max_model_len = 4096
        info.dtype = "bfloat16"
        return response

    async def GetModelInfo(
        self,
        request: openai_pb2.GetModelInfoRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ModelInfo:
        model_id = request.id or self._model_name
        if model_id != self._model_name:
            await context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Model '{model_id}' is not available in the dummy backend.",
            )
        return openai_pb2.ModelInfo(
            id=self._model_name,
            object="model",
            created=int(time.time()),
            owned_by="dummy-vllm",
            max_model_len=4096,
            dtype="bfloat16",
        )

    # ------------------------------------------------------------------
    # Chat completions
    # ------------------------------------------------------------------

    async def ChatCompletion(
        self,
        request: openai_pb2.ChatCompletionRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.ChatCompletionResponse:
        peer = context.peer()
        logger.info(f"{peer} - gRPC ChatCompletion - model: {request.model or self._model_name}")
        del context
        chat_request = converters.chat_request_from_proto(
            request,
            default_model=self._model_name,
            force_stream=False,
        )
        response = _build_chat_response(chat_request)
        metrics_collector.record_request(
            endpoint="/v1/chat/completions",
            tokens_generated=response.usage.completion_tokens if response.usage else 0,
        )
        return converters.chat_response_to_proto(response)

    async def ChatCompletionStream(
        self,
        request: openai_pb2.ChatCompletionRequest,
        context: aio.ServicerContext,
    ) -> AsyncIterator[openai_pb2.ChatCompletionChunk]:
        peer = context.peer()
        logger.info(f"{peer} - gRPC ChatCompletionStream - model: {request.model or self._model_name}")
        del context
        chat_request = converters.chat_request_from_proto(
            request,
            default_model=self._model_name,
            force_stream=True,
        )
        total_tokens = 0
        try:
            async for chunk, emitted in _chat_chunk_stream(chat_request):
                total_tokens += emitted
                yield chunk
        finally:
            metrics_collector.record_request(
                endpoint="/v1/chat/completions",
                tokens_generated=total_tokens,
            )

    # ------------------------------------------------------------------
    # Text completions
    # ------------------------------------------------------------------

    async def Completion(
        self,
        request: openai_pb2.CompletionRequest,
        context: aio.ServicerContext,
    ) -> openai_pb2.CompletionResponse:
        peer = context.peer()
        logger.info(f"{peer} - gRPC Completion - model: {request.model or self._model_name}")
        del context
        completion_request = converters.completion_request_from_proto(
            request,
            default_model=self._model_name,
            force_stream=False,
        )
        response = _build_completion_response(completion_request)
        metrics_collector.record_request(
            endpoint="/v1/completions",
            tokens_generated=response.usage.completion_tokens if response.usage else 0,
        )
        return converters.completion_response_to_proto(response)

    async def CompletionStream(
        self,
        request: openai_pb2.CompletionRequest,
        context: aio.ServicerContext,
    ) -> AsyncIterator[openai_pb2.CompletionChunk]:
        peer = context.peer()
        logger.info(f"{peer} - gRPC CompletionStream - model: {request.model or self._model_name}")
        del context
        completion_request = converters.completion_request_from_proto(
            request,
            default_model=self._model_name,
            force_stream=True,
        )
        total_tokens = 0
        try:
            async for chunk, emitted in _completion_chunk_stream(completion_request):
                total_tokens += emitted
                yield chunk
        finally:
            metrics_collector.record_request(
                endpoint="/v1/completions",
                tokens_generated=total_tokens,
            )


def build_grpc_server(
    *,
    host: str,
    port: int,
    max_message_megabytes: int = 32,
) -> Tuple[aio.Server, int]:
    """Construct the gRPC server and return it alongside the bound port."""
    options = [
        ("grpc.max_send_message_length", max_message_megabytes * 1024 * 1024),
        ("grpc.max_receive_message_length", max_message_megabytes * 1024 * 1024),
        ("grpc.keepalive_time_ms", 10_000),
        ("grpc.keepalive_timeout_ms", 5_000),
    ]
    server = aio.server(options=options)
    openai_pb2_grpc.add_VLLMServiceServicer_to_server(DummyGrpcServicer(), server)
    bound_port = server.add_insecure_port(f"{host}:{port}")
    if bound_port == 0:
        raise RuntimeError(f"Unable to bind gRPC server on {host}:{port}")
    return server, bound_port


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_completion_response(request: CompletionRequest) -> CompletionResponse:
    prompts = _normalize_prompts(request.prompt)
    choices = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    choice_index = 0

    for prompt_text in prompts:
        prompt_tokens = DummyTextGenerator.estimate_token_count(prompt_text)
        total_prompt_tokens += prompt_tokens
        for _ in range(request.n):
            generated_text = DummyTextGenerator.generate_completion_text(max_tokens=request.max_tokens)
            completion_tokens = DummyTextGenerator.estimate_token_count(generated_text)
            total_completion_tokens += completion_tokens
            choices.append(
                ResponseBuilder.completion_choice(
                    index=choice_index,
                    text=generated_text,
                    finish_reason="stop",
                )
            )
            choice_index += 1

    return ResponseBuilder.completion_response(
        model=request.model,
        choices=choices,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
    )


def _build_chat_response(request: ChatCompletionRequest) -> ChatCompletionResponse:
    prompt_text = _messages_to_prompt(request.messages)
    prompt_tokens = DummyTextGenerator.estimate_token_count(prompt_text)
    choices = []
    total_completion_tokens = 0

    for index in range(request.n):
        content = DummyTextGenerator.generate_completion_text(max_tokens=request.max_tokens)
        completion_tokens = DummyTextGenerator.estimate_token_count(content)
        total_completion_tokens += completion_tokens
        choices.append(
            ResponseBuilder.chat_choice(
                index=index,
                content=content,
                finish_reason="stop",
            )
        )

    return ResponseBuilder.chat_response(
        model=request.model,
        choices=choices,
        prompt_tokens=prompt_tokens,
        completion_tokens=total_completion_tokens,
    )


async def _completion_chunk_stream(
    request: CompletionRequest,
) -> AsyncIterator[Tuple[openai_pb2.CompletionChunk, int]]:
    prompts = _normalize_prompts(request.prompt)
    completion_id = ResponseBuilder.completion_id()
    choice_index = 0

    for _ in prompts:
        for _ in range(request.n):
            async for token in DummyTextGenerator.stream_tokens(max_tokens=request.max_tokens):
                chunk = converters.completion_chunk_from_choice(
                    completion_id=completion_id,
                    model=request.model,
                    choice_index=choice_index,
                    text=token,
                    finish_reason=None,
                )
                yield chunk, 1
            final_chunk = converters.completion_chunk_from_choice(
                completion_id=completion_id,
                model=request.model,
                choice_index=choice_index,
                text="",
                finish_reason="stop",
            )
            yield final_chunk, 0
            choice_index += 1

async def _chat_chunk_stream(
    request: ChatCompletionRequest,
) -> AsyncIterator[Tuple[openai_pb2.ChatCompletionChunk, int]]:
    completion_id = ResponseBuilder.completion_id()
    for choice_index in range(request.n):
        async for token in DummyTextGenerator.stream_tokens(max_tokens=request.max_tokens):
            chunk = converters.chat_chunk_from_delta(
                completion_id=completion_id,
                model=request.model,
                choice_index=choice_index,
                content=token,
                finish_reason=None,
            )
            yield chunk, 1
        final_chunk = converters.chat_chunk_from_delta(
            completion_id=completion_id,
            model=request.model,
            choice_index=choice_index,
            content="",
            finish_reason="stop",
        )
        yield final_chunk, 0


def _normalize_prompts(prompt: str | Iterable[str]) -> List[str]:
    if isinstance(prompt, str):
        return [prompt]
    prompts = list(prompt)
    if not prompts:
        return [""]
    return [text or "" for text in prompts]


def _messages_to_prompt(messages: List[ChatCompletionMessage]) -> str:
    if not messages:
        return ""
    joined: List[str] = []
    for message in messages:
        joined.append(f"{message.role}: {message.content}")
    return "\n".join(joined)


