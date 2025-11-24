#!/usr/bin/env python3
"""Tests for /v1/completions endpoint."""

# Standard library imports
import json

# Third-party imports
from fastapi.testclient import TestClient


def test_non_streaming_completion(client: TestClient) -> None:
    response = client.post(
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "Hello",
            "max_tokens": 8,
            "stream": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "text_completion"
    assert payload["choices"][0]["finish_reason"] in ("stop", "length")
    assert payload["usage"]["total_tokens"] >= 1


def test_streaming_completion(client: TestClient) -> None:
    chunks = []
    with client.stream(
        "POST",
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "stream me",
            "max_tokens": 4,
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
            chunks.append(json.loads(data))
    assert len(chunks) >= 1
    assert chunks[-1]["choices"][0]["finish_reason"] in (None, "stop", "length")


def test_completion_batch_and_multiple_choices(client: TestClient) -> None:
    response = client.post(
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": ["Hello", "World"],
            "max_tokens": 4,
            "n": 2,
            "stream": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["choices"]) == 4
    assert {choice["index"] for choice in payload["choices"]} == {0, 1, 2, 3}


def test_streaming_completion_multiple_choices(client: TestClient) -> None:
    seen_indexes = set()
    with client.stream(
        "POST",
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "stream me",
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
            seen_indexes.add(chunk["choices"][0]["index"])
    assert seen_indexes == {0, 1}


def test_completion_finish_reason_length(client: TestClient) -> None:
    response = client.post(
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "truncate me",
            "max_tokens": 1,
            "stream": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["choices"][0]["finish_reason"] == "length"


def test_streaming_completion_length_finish_reason(client: TestClient) -> None:
    final_chunk = None
    with client.stream(
        "POST",
        "/v1/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "truncate me",
            "max_tokens": 1,
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
            final_chunk = json.loads(data)
    assert final_chunk is not None
    assert final_chunk["choices"][0]["finish_reason"] == "length"
