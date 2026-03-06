"""Mindra orchestration API client."""

from __future__ import annotations

import time

import httpx


class MindraClient:
    """Calls Mindra hierarchical DAG orchestration endpoint."""

    def __init__(self, api_url: str, api_key: str, timeout_seconds: int):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def orchestrate(self, trace_id: str, dag: dict, context: dict) -> dict:
        payload = {
            "traceId": trace_id,
            "mode": "hierarchical_dag",
            "dag": dag,
            "context": context,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # pragma: no cover - network path
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Mindra orchestration failed after retries: {last_error}")
