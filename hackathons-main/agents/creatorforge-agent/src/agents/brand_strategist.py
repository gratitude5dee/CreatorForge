"""Brand strategist specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients


class BrandStrategistAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None) -> dict:
        prompt = (
            "You are CreatorForge Brand Strategist Agent. Generate a practical brand kit.\n"
            f"Brand: {brand or 'N/A'}\nAudience: {audience or 'General'}\nBrief: {brief}\n"
            "Provide voice, palette suggestions, typography direction, and positioning."
        )
        kit = self.openai.generate_text(prompt, max_tokens=700)
        return {"brand_kit": kit}
