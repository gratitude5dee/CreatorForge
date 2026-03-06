"""Designer specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients


class DesignerAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None) -> dict:
        image_prompt = (
            "Create a premium marketing visual. "
            f"Brand: {brand or 'N/A'}. Audience: {audience or 'General'}. Brief: {brief}."
        )
        image = self.openai.generate_image(image_prompt)
        return {
            "visual_prompt": image_prompt,
            "image": image,
        }
