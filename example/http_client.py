#!/usr/bin/env python3
"""Simple HTTP client to call the dummy vLLM REST endpoints."""

# Standard library imports
from __future__ import annotations

import json
from typing import Any

# Third-party imports
import requests


def _pretty_print(label: str, payload: Any) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    base_url = "http://localhost:8000/v1"

    response = requests.post(
        f"{base_url}/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "Say hello to the world",
            "max_tokens": 8,
            "stream": False,
        },
        timeout=5,
    )
    response.raise_for_status()
    _pretty_print("HTTP completion", response.json())

    response = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "Give me a fun fact"},
            ],
            "max_tokens": 6,
        },
        timeout=5,
    )
    response.raise_for_status()
    _pretty_print("HTTP chat completion", response.json())


if __name__ == "__main__":
    main()

