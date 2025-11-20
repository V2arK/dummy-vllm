#!/usr/bin/env python3
"""Simple HTTP client to call the dummy vLLM REST endpoints."""

# Standard library imports
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

# Third-party imports
import requests
from requests import exceptions as requests_exceptions

# Local/application imports
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _pretty_print(label: str, payload: Any) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _post_json(base_url: str, endpoint: str, payload: dict, label: str) -> None:
    try:
        response = requests.post(f"{base_url}{endpoint}", json=payload, timeout=5)
        response.raise_for_status()
    except requests_exceptions.Timeout:
        print(f"{label} request timed out")
        return
    except requests_exceptions.RequestException as exc:
        print(f"{label} request failed: {exc}")
        return
    _pretty_print(label, response.json())


def main() -> None:
    base_url = "http://localhost:8000/v1"

    _post_json(
        base_url,
        "/completions",
        {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "prompt": "Say hello to the world",
            "max_tokens": 8,
            "stream": False,
        },
        label="HTTP completion",
    )

    _post_json(
        base_url,
        "/chat/completions",
        {
            "model": "Qwen/Qwen2.5-VL-7B-Instruct",
            "messages": [
                {"role": "user", "content": "Give me a fun fact"},
            ],
            "max_tokens": 6,
        },
        label="HTTP chat completion",
    )


if __name__ == "__main__":
    main()

