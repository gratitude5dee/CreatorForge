"""Market scout specialist agent for external procurement."""

from __future__ import annotations

import httpx

from ..api.models import VendorCandidate
from ..integrations.nevermined_client import NeverminedClient


class MarketScoutAgent:
    """Purchases external services from A2A/HTTP sellers using x402 tokens."""

    def __init__(self, nevermined: NeverminedClient, timeout_seconds: int = 25):
        self.nevermined = nevermined
        self.timeout_seconds = timeout_seconds

    def discover_agent(self, base_url: str) -> dict:
        card_url = f"{base_url.rstrip('/')}/.well-known/agent.json"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(card_url)
        response.raise_for_status()
        return response.json()

    def purchase(self, vendor: VendorCandidate) -> tuple[dict, int]:
        token = self.nevermined.get_access_token(vendor.plan_id, vendor.agent_id)
        payload = {"query": vendor.query}
        headers = {"payment-signature": token}
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(vendor.endpoint, json=payload, headers=headers)

        if response.status_code >= 400:
            raise RuntimeError(f"vendor purchase failed for {vendor.vendor_id}: {response.status_code} {response.text}")

        body = response.json()
        credits = int(body.get("credits_used", vendor.expected_credits))
        return body, credits

    @staticmethod
    def extract_scores(response_body: dict, expected_credits: int) -> tuple[float, float, float, float]:
        quality = float(response_body.get("quality", 7.0))
        compliance = float(response_body.get("compliance", 7.0))
        latency_ms = float(response_body.get("latency_ms", 800.0))
        latency_score = max(1.0, min(10.0, round(10.0 - (latency_ms / 250.0), 2)))
        cost_efficiency = max(1.0, min(10.0, round(11.0 - expected_credits, 2)))
        return quality, compliance, latency_score, cost_efficiency
