"""Designer specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients
from .tooling import strands_tool


class DesignerAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None, ad_context: dict | None = None) -> dict:
        sponsor_guidance = ""
        if ad_context:
            sponsor_guidance = f" Include native sponsor context: {ad_context}."
        image_prompt = (
            "Create a premium marketing visual. "
            f"Brand: {brand or 'N/A'}. Audience: {audience or 'General'}. Brief: {brief}.{sponsor_guidance}"
        )
        image = self.openai.generate_image(image_prompt)
        return {
            "visual_prompt": image_prompt,
            "image": image,
        }

    def as_tool(self):
        @strands_tool
        def generate_visual_asset(brief: str, brand: str = "", audience: str = "", ad_context: str = "") -> dict:
            parsed_context = {"raw": ad_context} if ad_context else None
            return self.run(brief, brand or None, audience or None, parsed_context)

        return generate_visual_asset
