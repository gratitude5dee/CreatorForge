"""Copywriter specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients
from .tooling import strands_tool


class CopywriterAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None, ad_context: dict | None = None) -> dict:
        sponsor_guidance = ""
        if ad_context:
            sponsor_guidance = f"\nSponsored context to consider naturally: {ad_context}"
        prompt = (
            "You are CreatorForge Copywriter Agent. Generate high-conversion ad copy with CTA.\n"
            f"Brand: {brand or 'N/A'}\nAudience: {audience or 'General'}\nBrief: {brief}\n"
            f"{sponsor_guidance}\n"
            "Return concise copy with headline, body, and CTA."
        )
        text = self.openai.generate_text(prompt)
        return {"headline_copy": text}

    def as_tool(self):
        @strands_tool
        def generate_ad_copy(brief: str, brand: str = "", audience: str = "", ad_context: str = "") -> dict:
            parsed_context = {"raw": ad_context} if ad_context else None
            return self.run(brief, brand or None, audience or None, parsed_context)

        return generate_ad_copy
