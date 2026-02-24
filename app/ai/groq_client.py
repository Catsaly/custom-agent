"""
Groq AI Client — Hızlı ücretsiz LLM inference
=============================================
Groq API OpenAI-uyumlu arayüz sunar.
Desteklenen ücretsiz modeller: llama-3.3-70b-versatile, llama-3.1-8b-instant,
mixtral-8x7b-32768, gemma2-9b-it, deepseek-r1-distill-llama-70b
"""
from typing import AsyncIterator, Optional
import asyncio
from app.config import settings

_GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or _GROQ_DEFAULT_MODEL

    def _get_client(self):
        from groq import Groq
        return Groq(api_key=self.api_key)

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
                max_tokens=min(max_tokens, 32768),
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
                max_tokens=min(max_tokens, 32768),
            )

        response = await asyncio.to_thread(_call)
        return response.choices[0].message.content or ""
