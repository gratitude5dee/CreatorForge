"""Ad revenue specialist agent."""

from __future__ import annotations

from ..integrations.zeroclick_client import ZeroClickClient
from ..storage.repository import Repository
from .tooling import strands_tool


class AdRevenueAgent:
    def __init__(self, zeroclick: ZeroClickClient, repo: Repository):
        self.zeroclick = zeroclick
        self.repo = repo

    def enrich(self, prompt: str, audience: str | None, trace_id: str) -> dict:
        context = self.zeroclick.fetch_context(prompt=prompt, audience=audience, placement="creative-output")
        self.zeroclick.track_event("considered", {"trace_id": trace_id, "context": context})
        self.repo.record_ad_event(
            trace_id,
            "considered",
            "zeroclick",
            {"trace_id": trace_id, "context": context, "idempotency_key": f"ad:considered:{trace_id}"},
        )
        return context

    def mark_included(self, trace_id: str, context: dict) -> None:
        self.repo.record_ad_event(
            trace_id,
            "included",
            "zeroclick",
            {"trace_id": trace_id, "context": context, "idempotency_key": f"ad:included:{trace_id}"},
        )
        self.zeroclick.track_event("included", {"trace_id": trace_id, "context": context})

    def track_callback(self, trace_id: str, event: str, payload: dict) -> None:
        self.repo.record_ad_event(
            trace_id,
            event,
            "zeroclick",
            {"trace_id": trace_id, "payload": payload, "idempotency_key": f"ad:{event}:{trace_id}"},
        )
        self.zeroclick.track_event(event, {"trace_id": trace_id, "payload": payload})

    def as_tool(self):
        @strands_tool
        def fetch_native_ad_context(prompt: str, audience: str = "", trace_id: str = "") -> dict:
            return self.enrich(prompt, audience or None, trace_id)

        return fetch_native_ad_context
