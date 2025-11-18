#!/usr/bin/env python3
"""Tests for /v1/chat/completions endpoint."""

# Standard library imports
import json

# Third-party imports
from fastapi.testclient import TestClient


def test_chat_completion(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "hello"},
            ],
            "max_tokens": 6,
            "stream": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert payload["usage"]["total_tokens"] >= 1


def test_chat_streaming_completion(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "stream please"},
            ],
            "max_tokens": 5,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        lines = []
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            lines.append(line)
    assert any("data: [DONE]" in line for line in lines)


def test_chat_multiple_choices(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "hello"},
            ],
            "max_tokens": 3,
            "n": 2,
            "stream": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["choices"]) == 2
    assert {choice["index"] for choice in payload["choices"]} == {0, 1}


def test_chat_streaming_multiple_choices(client: TestClient) -> None:
    indexes = set()
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "stream please"},
            ],
            "max_tokens": 3,
            "n": 2,
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            indexes.add(chunk["choices"][0]["index"])
    assert indexes == {0, 1}

