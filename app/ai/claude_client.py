"""Claude (Anthropic) AI client with streaming support."""
import anthropic
from typing import AsyncIterator, Optional
from app.config import settings


class ClaudeClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
        self.model = "claude-opus-4-6"

    async def stream_chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "thinking": {"type": "adaptive"},
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "thinking": {"type": "adaptive"},
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        async with self.client.messages.stream(**kwargs) as stream:
            response = await stream.get_final_message()
        return next(
            (b.text for b in response.content if b.type == "text"), ""
        )

    async def analyze_image(self, image_data: str, media_type: str, prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return next(
            (b.text for b in response.content if b.type == "text"), ""
        )
