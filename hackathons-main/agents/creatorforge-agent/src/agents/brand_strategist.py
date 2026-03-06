"""Brand strategist specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients
from .tooling import strands_tool


class BrandStrategistAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None, ad_context: dict | None = None) -> dict:
        sponsor_guidance = ""
        if ad_context:
            sponsor_guidance = f"\nRelevant sponsor context: {ad_context}"
        prompt = (
            "You are CreatorForge Brand Strategist Agent. Generate a practical brand kit.\n"
            f"Brand: {brand or 'N/A'}\nAudience: {audience or 'General'}\nBrief: {brief}\n"
            f"{sponsor_guidance}\n"
            "Provide voice, palette suggestions, typography direction, and positioning."
        )
        kit = self.openai.generate_text(prompt, max_tokens=700)
        return {"brand_kit": kit}

    def as_tool(self):
        @strands_tool
        def generate_brand_kit(brief: str, brand: str = "", audience: str = "", ad_context: str = "") -> dict:
            parsed_context = {"raw": ad_context} if ad_context else None
            return self.run(brief, brand or None, audience or None, parsed_context)

        return generate_brand_kit
