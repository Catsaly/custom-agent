"""
OpenRouter Client — Ücretsiz ve ücretli modellere tek API
=========================================================
OpenRouter, OpenAI-uyumlu API ile çok sayıda modele erişim sağlar.
Ücretsiz modeller ':free' suffix'i ile kullanılabilir.
Kayıt: https://openrouter.ai
"""
from typing import AsyncIterator, Optional
import asyncio
from app.config import settings

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "google/gemini-2.0-flash-exp:free"


class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.model = model or _DEFAULT_MODEL

    def _get_client(self):
        from openai import OpenAI
        return OpenAI(
            api_key=self.api_key,
            base_url=_OPENROUTER_BASE_URL,
        )

    def _build_messages(
        self, messages: list[dict], system: Optional[str] = None
    ) -> list[dict]:
        result = []
        if system:
            result.append({"role": "system", "content": system})
        for msg in messages:
            role = msg.get("role", "user")
            if role not in ("user", "assistant", "system"):
                role = "user"
            result.append({"role": role, "content": msg.get("content", "")})
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
                extra_headers={
                    "HTTP-Referer": "https://nightowl-charm.lovable.app",
                    "X-Title": "Milli Yapay Zeka IDE",
                },
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
                extra_headers={
                    "HTTP-Referer": "https://nightowl-charm.lovable.app",
                    "X-Title": "Milli Yapay Zeka IDE",
                },
            )

        response = await asyncio.to_thread(_call)
        return response.choices[0].message.content or ""
