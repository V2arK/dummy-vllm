#!/usr/bin/env python3
"""OpenAI-compatible /v1/chat/completions endpoint."""

# Standard library imports
import json
from typing import AsyncGenerator, List, Union

# Third-party imports
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# Local/application imports
from src.generators.dummy_generator import DummyTextGenerator
from src.generators.response_builder import ResponseBuilder
from src.models import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from src.utils.metrics import metrics_collector


router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
) -> Union[ChatCompletionResponse, StreamingResponse]:
    """Handle chat completions with optional streaming."""
    prompt_text = _messages_to_prompt(request.messages)
    if request.stream:
        return await _streaming_chat_completion(request)

    prompt_tokens = DummyTextGenerator.estimate_token_count(prompt_text)
    choices: List[ChatCompletionChoice] = []
    total_completion_tokens = 0
    for index in range(request.n):
        generated_text, truncated = DummyTextGenerator.generate_completion_with_metadata(
            max_tokens=request.max_tokens
        )
        completion_tokens = DummyTextGenerator.estimate_token_count(generated_text)
        total_completion_tokens += completion_tokens
        choices.append(
            ResponseBuilder.chat_choice(
                index=index,
                content=generated_text,
                finish_reason="length" if truncated else "stop",
            )
        )
    response = ResponseBuilder.chat_response(
        model=request.model,
        choices=choices,
        prompt_tokens=prompt_tokens,
        completion_tokens=total_completion_tokens,
    )
    metrics_collector.record_request(endpoint="/v1/chat/completions", tokens_generated=total_completion_tokens)
    return response


async def _streaming_chat_completion(request: ChatCompletionRequest) -> StreamingResponse:
    completion_id = ResponseBuilder.completion_id()

    async def event_generator() -> AsyncGenerator[str, None]:
        total_completion_tokens = 0
        try:
            for choice_index in range(request.n):
                tokens, truncated = DummyTextGenerator.prepare_token_stream(max_tokens=request.max_tokens)
                async for token in DummyTextGenerator.stream_from_tokens(tokens):
                    total_completion_tokens += 1
                    chunk = ResponseBuilder.chat_stream_chunk(
                        completion_id=completion_id,
                        model=request.model,
                        choice_index=choice_index,
                        token_text=token,
                        finish_reason=None,
                    )
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                final_chunk = ResponseBuilder.chat_stream_chunk(
                    completion_id=completion_id,
                    model=request.model,
                    choice_index=choice_index,
                    token_text="",
                    finish_reason="length" if truncated else "stop",
                )
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            metrics_collector.record_request(
                endpoint="/v1/chat/completions",
                tokens_generated=total_completion_tokens,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _messages_to_prompt(messages: List[ChatCompletionMessage]) -> str:
    """Concatenate chat messages into a single prompt string."""
    if not messages:
        return ""
    joined = []
    for message in messages:
        joined.append(f"{message.role}: {message.content}")
    return "\n".join(joined)

