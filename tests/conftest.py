#!/usr/bin/env python3
"""Pytest fixtures for API tests."""

# Third-party imports
import pytest
from fastapi.testclient import TestClient

# Local/application imports
from src.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)

