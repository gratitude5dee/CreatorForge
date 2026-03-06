"""Copywriter specialist agent."""

from __future__ import annotations

from ..integrations.openai_clients import OpenAIClients


class CopywriterAgent:
    def __init__(self, openai_clients: OpenAIClients):
        self.openai = openai_clients

    def run(self, brief: str, brand: str | None, audience: str | None) -> dict:
        prompt = (
            "You are CreatorForge Copywriter Agent. Generate high-conversion ad copy with CTA.\n"
            f"Brand: {brand or 'N/A'}\nAudience: {audience or 'General'}\nBrief: {brief}\n"
            "Return concise copy with headline, body, and CTA."
        )
        text = self.openai.generate_text(prompt)
        return {"headline_copy": text}
