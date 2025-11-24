#!/usr/bin/env python3
"""Lightweight in-memory metrics for request accounting."""

# Standard library imports
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict


@dataclass
class MetricsSnapshot:
    """Immutable view of collected metrics."""

    total_requests: int
    requests_by_endpoint: Dict[str, int]
    total_tokens_generated: int


class MetricsCollector:
    """Thread-safe collector for basic request metrics."""

    def __init__(self) -> None:
        self._request_counts: DefaultDict[str, int] = defaultdict(int)
        self._total_tokens_generated = 0
        self._lock = threading.Lock()

    def record_request(self, endpoint: str, tokens_generated: int) -> None:
        """Record a processed request for the given endpoint."""
        with self._lock:
            self._request_counts[endpoint] += 1
            self._total_tokens_generated += tokens_generated

    def snapshot(self) -> MetricsSnapshot:
        """Return a snapshot of the collected metrics."""
        with self._lock:
            total_requests = sum(self._request_counts.values())
            requests_by_endpoint = dict(self._request_counts)
            total_tokens_generated = self._total_tokens_generated
        return MetricsSnapshot(
            total_requests=total_requests,
            requests_by_endpoint=requests_by_endpoint,
            total_tokens_generated=total_tokens_generated,
        )


metrics_collector = MetricsCollector()
