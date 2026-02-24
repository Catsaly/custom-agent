"""
AI Client Factory — Model ID'ye göre doğru client'ı döner
=========================================================
Kullanım:
    client = get_client_for_model("llama-3.3-70b-versatile", api_key="gsk_...")
    response = await client.chat(messages, system=system_prompt)
"""
from typing import Optional
from app.ai.model_registry import get_model, resolve_model_id, MODELS


def get_client_for_model(model_id: str, api_key: Optional[str] = None):
    """
    Model ID'ye göre uygun AI client örneği döner.
    api_key verilmişse settings yerine onu kullanır.
    """
    model_id = resolve_model_id(model_id)
    info = get_model(model_id)
    if not info:
        # Fallback: claude
        from app.ai.claude_client import ClaudeClient
        return ClaudeClient(api_key=api_key)

    provider = info["provider"]

    if provider == "anthropic":
        from app.ai.claude_client import ClaudeClient
        return ClaudeClient(api_key=api_key, model=model_id)

    elif provider == "gemini":
        from app.ai.gemini_client import GeminiClient
        return GeminiClient(api_key=api_key, model=model_id)

    elif provider == "glm":
        from app.ai.glm_client import GLMClient
        return GLMClient(api_key=api_key, model=model_id)

    elif provider == "groq":
        from app.ai.groq_client import GroqClient
        return GroqClient(api_key=api_key, model=model_id)

    elif provider == "openrouter":
        from app.ai.openrouter_client import OpenRouterClient
        return OpenRouterClient(api_key=api_key, model=model_id)

    else:
        from app.ai.claude_client import ClaudeClient
        return ClaudeClient(api_key=api_key)


def get_client_legacy(provider: str, api_key: Optional[str] = None, model_id: Optional[str] = None):
    """
    Eski 'claude'/'gemini'/'glm' kısa isimlerini destekler.
    """
    from app.ai.model_registry import LEGACY_MAP
    resolved = LEGACY_MAP.get(provider, provider)
    final_model = model_id or resolved
    return get_client_for_model(final_model, api_key=api_key)
