"""Ad revenue specialist agent."""

from __future__ import annotations

from ..integrations.zeroclick_client import ZeroClickClient


class AdRevenueAgent:
    def __init__(self, zeroclick: ZeroClickClient):
        self.zeroclick = zeroclick

    def enrich(self, prompt: str, audience: str | None, trace_id: str) -> tuple[dict, dict]:
        context = self.zeroclick.fetch_context(prompt=prompt, audience=audience, placement="creative-output")
        self.zeroclick.track_event("considered", {"trace_id": trace_id, "context": context})
        return (
            {
                "sponsored_context": context,
                "placement": "creative-output",
            },
            context,
        )
