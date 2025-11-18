#!/usr/bin/env python3
"""Tests for /v1/models endpoint."""

# Third-party imports
from fastapi.testclient import TestClient


def test_list_models(client: TestClient) -> None:
    response = client.get("/v1/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert len(payload["data"]) >= 1

