"""Google Gemini AI client with streaming support."""
import google.generativeai as genai
from typing import AsyncIterator, Optional
import asyncio
from app.config import settings

_DEFAULT_MODEL = "gemini-2.0-flash-exp"


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.google_api_key
        self.model_name = model or _DEFAULT_MODEL
        self.vision_model_name = "gemini-1.5-pro"
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _get_model(self, system: Optional[str] = None):
        config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
        }
        kwargs = {"generation_config": config}
        if system:
            kwargs["system_instruction"] = system
        if self.api_key:
            genai.configure(api_key=self.api_key)
        return genai.GenerativeModel(self.model_name, **kwargs)

    async def stream_chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> AsyncIterator[str]:
        model = self._get_model(system)
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        last_msg = messages[-1]["content"]

        response = await asyncio.to_thread(
            chat.send_message, last_msg, stream=True
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> str:
        model = self._get_model(system)
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        last_msg = messages[-1]["content"]

        response = await asyncio.to_thread(chat.send_message, last_msg)
        return response.text

    async def analyze_image(self, image_data: bytes, prompt: str) -> str:
        import PIL.Image
        import io
        if self.api_key:
            genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.vision_model_name)
        image = PIL.Image.open(io.BytesIO(image_data))
        response = await asyncio.to_thread(
            model.generate_content, [prompt, image]
        )
        return response.text
