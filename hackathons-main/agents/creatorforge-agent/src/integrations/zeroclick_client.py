"""ZeroClick live API client."""

from __future__ import annotations

import httpx


class ZeroClickClient:
    """Calls ZeroClick for context and attribution events."""

    def __init__(self, base_url: str, api_key: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def fetch_context(self, prompt: str, audience: str | None, placement: str) -> dict:
        payload = {
            "prompt": prompt,
            "audience": audience,
            "placement": placement,
        }
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/context", headers=self._headers(), json=payload)
        response.raise_for_status()
        return response.json()

    def fetch_marketplace_slots(self, category: str) -> dict:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(
                f"{self.base_url}/marketplace/slots",
                headers=self._headers(),
                params={"category": category},
            )
        response.raise_for_status()
        return response.json()

    def track_event(self, event: str, payload: dict) -> dict:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/events",
                headers=self._headers(),
                json={"event": event, "payload": payload},
            )
        response.raise_for_status()
        return response.json()
