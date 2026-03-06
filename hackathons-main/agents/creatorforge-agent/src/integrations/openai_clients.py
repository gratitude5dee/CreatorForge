"""OpenAI text and image generation wrappers."""

from __future__ import annotations

from openai import OpenAI


class OpenAIClients:
    """Simple wrappers used by specialist agents."""

    def __init__(self, api_key: str, text_model: str, image_model: str):
        self.client = OpenAI(api_key=api_key)
        self.text_model = text_model
        self.image_model = image_model

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        response = self.client.responses.create(
            model=self.text_model,
            input=prompt,
            max_output_tokens=max_tokens,
        )
        text = getattr(response, "output_text", "")
        if not text:
            raise RuntimeError("OpenAI text generation returned empty output")
        return text

    def generate_image(self, prompt: str, size: str = "1024x1024") -> dict:
        response = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=size,
        )
        data = response.data[0]
        return {
            "url": getattr(data, "url", None),
            "b64_json": getattr(data, "b64_json", None),
            "revised_prompt": getattr(data, "revised_prompt", prompt),
        }
