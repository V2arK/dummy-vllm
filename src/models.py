#!/usr/bin/env python3
"""Pydantic models that mirror vLLM's OpenAI-compatible schema."""

# Standard library imports
from typing import Dict, List, Optional, Sequence, Union

# Third-party imports
from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, Sequence[str]]
    max_tokens: int = Field(default=16, ge=1)
    temperature: float = 1.0
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    logprobs: Optional[int] = None
    echo: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    best_of: Optional[int] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatCompletionMessage]
    max_tokens: int = Field(default=16, ge=1)
    temperature: float = 1.0
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    user: Optional[str] = None


class CompletionChoice(BaseModel):
    index: int
    text: str
    logprobs: Optional[dict]
    finish_reason: Optional[str]


class CompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: Optional[CompletionUsage]


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str]


class ChatCompletionStreamChoice(BaseModel):
    index: int
    delta: ChatCompletionMessage
    finish_reason: Optional[str]


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[CompletionUsage]
