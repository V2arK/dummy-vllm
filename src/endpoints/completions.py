#!/usr/bin/env python3
"""OpenAI-compatible /v1/completions endpoint."""

# Standard library imports
import json
from typing import AsyncGenerator, List, Sequence, Union

# Third-party imports
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# Local/application imports
from src.generators.dummy_generator import DummyTextGenerator
from src.generators.response_builder import ResponseBuilder
from src.models import CompletionChoice, CompletionRequest, CompletionResponse
from src.utils.metrics import metrics_collector


router = APIRouter()


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest,
) -> Union[CompletionResponse, StreamingResponse]:
    """Handle completion requests with optional streaming."""
    prompts = _normalize_prompts(request.prompt)
    if request.stream:
        return await _streaming_completion(request, prompts)

    choices: List[CompletionChoice] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    choice_index = 0

    for prompt_text in prompts:
        prompt_tokens = DummyTextGenerator.estimate_token_count(prompt_text)
        total_prompt_tokens += prompt_tokens
        for _ in range(request.n):
            generated_text, truncated = (
                DummyTextGenerator.generate_completion_with_metadata(
                    max_tokens=request.max_tokens
                )
            )
            completion_tokens = DummyTextGenerator.estimate_token_count(generated_text)
            total_completion_tokens += completion_tokens
            choices.append(
                ResponseBuilder.completion_choice(
                    index=choice_index,
                    text=generated_text,
                    finish_reason="length" if truncated else "stop",
                )
            )
            choice_index += 1

    response = ResponseBuilder.completion_response(
        model=request.model,
        choices=choices,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
    )
    metrics_collector.record_request(
        endpoint="/v1/completions", tokens_generated=total_completion_tokens
    )
    return response


async def _streaming_completion(
    request: CompletionRequest, prompts: List[str]
) -> StreamingResponse:
    """Return a streaming response for the completion endpoint."""
    completion_id = ResponseBuilder.completion_id()

    async def event_generator() -> AsyncGenerator[str, None]:
        total_completion_tokens = 0
        choice_index = 0
        try:
            for _ in prompts:
                for _ in range(request.n):
                    tokens, truncated = DummyTextGenerator.prepare_token_stream(
                        max_tokens=request.max_tokens
                    )
                    async for token in DummyTextGenerator.stream_from_tokens(tokens):
                        total_completion_tokens += 1
                        chunk = ResponseBuilder.completion_stream_chunk(
                            completion_id=completion_id,
                            model=request.model,
                            choice_index=choice_index,
                            token_text=token,
                            finish_reason=None,
                        )
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    final_chunk = ResponseBuilder.completion_stream_chunk(
                        completion_id=completion_id,
                        model=request.model,
                        choice_index=choice_index,
                        token_text="",
                        finish_reason="length" if truncated else "stop",
                    )
                    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                    choice_index += 1
            yield "data: [DONE]\n\n"
        finally:
            metrics_collector.record_request(
                endpoint="/v1/completions",
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


def _normalize_prompts(prompt: Union[str, Sequence[str]]) -> List[str]:
    """Normalize prompt input into a list of strings."""
    if isinstance(prompt, str):
        return [prompt]
    prompts = list(prompt)
    if not prompts:
        return [""]
    return [text or "" for text in prompts]
