"""ZhipuAI GLM client with streaming support."""
from typing import AsyncIterator, Optional
import asyncio
from app.config import settings


class GLMClient:
    def __init__(self):
        self.api_key = settings.zhipuai_api_key
        self.model = "glm-4-plus"
        self._client = None

    def _get_client(self):
        if self._client is None:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    def _build_messages(
        self, messages: list[dict], system: Optional[str] = None
    ) -> list[dict]:
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            result.append({"role": msg["role"], "content": msg["content"]})
        return result

    async def stream_chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        built = self._build_messages(messages, system)

        def _stream():
            return client.chat.completions.create(
                model=self.model,
                messages=built,
                stream=True,
                max_tokens=max_tokens,
            )

        response = await asyncio.to_thread(_stream)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        client = self._get_client()
        built = self._build_messages(messages, system)

        def _call():
            return client.chat.completions.create(
                model=self.model,
                messages=built,
                max_tokens=max_tokens,
            )

        response = await asyncio.to_thread(_call)
        return response.choices[0].message.content or ""

    async def analyze_image(self, image_base64: str, prompt: str) -> str:
        client = self._get_client()

        def _call():
            return client.chat.completions.create(
                model="glm-4v-plus",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            )

        response = await asyncio.to_thread(_call)
        return response.choices[0].message.content or ""
