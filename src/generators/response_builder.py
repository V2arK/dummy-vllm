#!/usr/bin/env python3
"""Builders that assemble vLLM-compatible response payloads."""

# Standard library imports
import time
import uuid
from typing import List, Optional

# Local/application imports
from src.models import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionResponse,
    ChatCompletionStreamChoice,
    CompletionChoice,
    CompletionResponse,
    CompletionUsage,
)


class ResponseBuilder:
    """Factory helpers for structured completion responses."""

    @staticmethod
    def completion_response(
        model: str,
        choices: List[CompletionChoice],
        prompt_tokens: int,
        completion_tokens: int,
    ) -> CompletionResponse:
        completion_id = ResponseBuilder.completion_id()
        created = int(time.time())
        usage = CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return CompletionResponse(
            id=completion_id,
            object="text_completion",
            created=created,
            model=model,
            choices=choices,
            usage=usage,
        )

    @staticmethod
    def completion_stream_chunk(
        completion_id: str,
        model: str,
        choice_index: int,
        token_text: str,
        finish_reason: Optional[str],
    ) -> dict:
        created = int(time.time())
        return {
            "id": completion_id,
            "object": "text_completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": choice_index,
                    "text": token_text,
                    "logprobs": None,
                    "finish_reason": finish_reason,
                }
            ],
        }

    @staticmethod
    def chat_response(
        model: str,
        choices: List[ChatCompletionChoice],
        prompt_tokens: int,
        completion_tokens: int,
    ) -> ChatCompletionResponse:
        completion_id = ResponseBuilder.completion_id()
        created = int(time.time())
        usage = CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        return ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=created,
            model=model,
            choices=choices,
            usage=usage,
        )

    @staticmethod
    def chat_stream_chunk(
        completion_id: str,
        model: str,
        choice_index: int,
        token_text: str,
        finish_reason: Optional[str],
    ) -> dict:
        created = int(time.time())
        choice = ChatCompletionStreamChoice(
            index=choice_index,
            delta=ChatCompletionMessage(role="assistant", content=token_text),
            finish_reason=finish_reason,
        )
        return {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [choice.model_dump()],
        }

    @staticmethod
    def completion_id() -> str:
        return f"cmpl-{uuid.uuid4().hex[:24]}"

    @staticmethod
    def completion_choice(index: int, text: str, finish_reason: Optional[str]) -> CompletionChoice:
        return CompletionChoice(index=index, text=text, logprobs=None, finish_reason=finish_reason)

    @staticmethod
    def chat_choice(index: int, content: str, finish_reason: Optional[str]) -> ChatCompletionChoice:
        message = ChatCompletionMessage(role="assistant", content=content)
        return ChatCompletionChoice(index=index, message=message, finish_reason=finish_reason)

