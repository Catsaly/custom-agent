"""
Model Registry — Tüm desteklenen AI modelleri
=============================================
Her model için: provider, display adı, model_id, ücretsiz mi, hangi API anahtarı.
"""
from typing import Optional

# ── Model Tanımları ──────────────────────────────────────────────────────────

MODELS: dict[str, dict] = {
    # ── Claude (Anthropic) ────────────────────────────────────────────────────
    "claude-opus-4-6": {
        "provider": "anthropic",
        "display": "Claude Opus 4.6",
        "short": "Opus 4.6",
        "free": False,
        "key_field": "anthropic",
        "icon": "🔶",
        "color": "#ff6b35",
        "group": "Claude",
    },
    "claude-sonnet-4-5": {
        "provider": "anthropic",
        "display": "Claude Sonnet 4.5",
        "short": "Sonnet 4.5",
        "free": False,
        "key_field": "anthropic",
        "icon": "🔶",
        "color": "#ff6b35",
        "group": "Claude",
    },
    "claude-haiku-3-5-20241022": {
        "provider": "anthropic",
        "display": "Claude Haiku 3.5",
        "short": "Haiku 3.5",
        "free": False,
        "key_field": "anthropic",
        "icon": "🔶",
        "color": "#ff6b35",
        "group": "Claude",
    },

    # ── Gemini (Google) ───────────────────────────────────────────────────────
    "gemini-2.0-flash": {
        "provider": "gemini",
        "display": "Gemini 2.0 Flash",
        "short": "Gemini 2.0",
        "free": True,
        "key_field": "google",
        "icon": "💎",
        "color": "#4285f4",
        "group": "Gemini",
    },
    "gemini-2.0-flash-exp": {
        "provider": "gemini",
        "display": "Gemini 2.0 Flash Exp",
        "short": "Gemini 2.0 Exp",
        "free": True,
        "key_field": "google",
        "icon": "💎",
        "color": "#4285f4",
        "group": "Gemini",
    },
    "gemini-1.5-flash": {
        "provider": "gemini",
        "display": "Gemini 1.5 Flash",
        "short": "Gemini 1.5",
        "free": True,
        "key_field": "google",
        "icon": "💎",
        "color": "#4285f4",
        "group": "Gemini",
    },
    "gemini-1.5-pro": {
        "provider": "gemini",
        "display": "Gemini 1.5 Pro",
        "short": "Gemini Pro",
        "free": False,
        "key_field": "google",
        "icon": "💎",
        "color": "#4285f4",
        "group": "Gemini",
    },

    # ── GLM (ZhipuAI) ─────────────────────────────────────────────────────────
    "glm-4-flash": {
        "provider": "glm",
        "display": "GLM-4 Flash (Ücretsiz)",
        "short": "GLM-4 Flash",
        "free": True,
        "key_field": "zhipuai",
        "icon": "🌊",
        "color": "#00c4cc",
        "group": "GLM",
    },
    "glm-4-plus": {
        "provider": "glm",
        "display": "GLM-4 Plus",
        "short": "GLM-4+",
        "free": False,
        "key_field": "zhipuai",
        "icon": "🌊",
        "color": "#00c4cc",
        "group": "GLM",
    },
    "glm-4": {
        "provider": "glm",
        "display": "GLM-4",
        "short": "GLM-4",
        "free": False,
        "key_field": "zhipuai",
        "icon": "🌊",
        "color": "#00c4cc",
        "group": "GLM",
    },

    # ── Groq (Hızlı Ücretsiz) ────────────────────────────────────────────────
    "llama-3.3-70b-versatile": {
        "provider": "groq",
        "display": "Llama 3.3 70B (Groq)",
        "short": "Llama 3.3 70B",
        "free": True,
        "key_field": "groq",
        "icon": "🦙",
        "color": "#7c3aed",
        "group": "Groq",
    },
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "display": "Llama 3.1 8B Instant (Groq)",
        "short": "Llama 3.1 8B",
        "free": True,
        "key_field": "groq",
        "icon": "🦙",
        "color": "#7c3aed",
        "group": "Groq",
    },
    "mixtral-8x7b-32768": {
        "provider": "groq",
        "display": "Mixtral 8x7B (Groq)",
        "short": "Mixtral 8x7B",
        "free": True,
        "key_field": "groq",
        "icon": "🦙",
        "color": "#7c3aed",
        "group": "Groq",
    },
    "gemma2-9b-it": {
        "provider": "groq",
        "display": "Gemma 2 9B (Groq)",
        "short": "Gemma 2 9B",
        "free": True,
        "key_field": "groq",
        "icon": "🦙",
        "color": "#7c3aed",
        "group": "Groq",
    },
    "deepseek-r1-distill-llama-70b": {
        "provider": "groq",
        "display": "DeepSeek R1 Distill 70B (Groq)",
        "short": "DeepSeek R1",
        "free": True,
        "key_field": "groq",
        "icon": "🦙",
        "color": "#7c3aed",
        "group": "Groq",
    },

    # ── OpenRouter (Ücretsiz modeller) ───────────────────────────────────────
    "google/gemini-2.0-flash-exp:free": {
        "provider": "openrouter",
        "display": "Gemini 2.0 Flash (OR)",
        "short": "Gemini 2.0",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "meta-llama/llama-3.3-70b-instruct:free": {
        "provider": "openrouter",
        "display": "Llama 3.3 70B (OR)",
        "short": "Llama 3.3 70B",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "deepseek/deepseek-chat-v3-0324:free": {
        "provider": "openrouter",
        "display": "DeepSeek V3 (OR)",
        "short": "DeepSeek V3",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "deepseek/deepseek-r1:free": {
        "provider": "openrouter",
        "display": "DeepSeek R1 (OR)",
        "short": "DeepSeek R1",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "qwen/qwq-32b:free": {
        "provider": "openrouter",
        "display": "QwQ 32B (OR)",
        "short": "QwQ 32B",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "qwen/qwen-2.5-72b-instruct:free": {
        "provider": "openrouter",
        "display": "Qwen 2.5 72B (OR)",
        "short": "Qwen 2.5 72B",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "microsoft/phi-4:free": {
        "provider": "openrouter",
        "display": "Phi-4 (OR)",
        "short": "Phi-4",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
    "mistralai/mistral-small-3.1-24b-instruct:free": {
        "provider": "openrouter",
        "display": "Mistral Small 3.1 24B (OR)",
        "short": "Mistral Small 3.1",
        "free": True,
        "key_field": "openrouter",
        "icon": "🌐",
        "color": "#059669",
        "group": "OpenRouter",
    },
}

# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def get_model(model_id: str) -> Optional[dict]:
    """Model bilgisini döner."""
    return MODELS.get(model_id)


def get_provider(model_id: str) -> Optional[str]:
    """Model'in provider'ını döner."""
    m = MODELS.get(model_id)
    return m["provider"] if m else None


def list_by_group() -> dict[str, list[tuple[str, dict]]]:
    """Modelleri gruba göre listeler: {group: [(model_id, info), ...]}"""
    groups: dict[str, list] = {}
    for mid, info in MODELS.items():
        g = info["group"]
        groups.setdefault(g, []).append((mid, info))
    return groups


def list_free() -> list[tuple[str, dict]]:
    """Sadece ücretsiz modelleri listeler."""
    return [(mid, info) for mid, info in MODELS.items() if info["free"]]


def list_paid() -> list[tuple[str, dict]]:
    """Sadece ücretli modelleri listeler."""
    return [(mid, info) for mid, info in MODELS.items() if not info["free"]]


def get_key_field(model_id: str) -> Optional[str]:
    """Model için gereken API key alanını döner."""
    m = MODELS.get(model_id)
    return m["key_field"] if m else None


# ── Select Options ────────────────────────────────────────────────────────────

def get_select_options(filter_free: Optional[bool] = None) -> list[str]:
    """Streamlit selectbox için model_id listesi."""
    result = []
    for mid, info in MODELS.items():
        if filter_free is None or info["free"] == filter_free:
            result.append(mid)
    return result


def get_display_name(model_id: str) -> str:
    """Model'in görünen adını döner."""
    m = MODELS.get(model_id)
    if not m:
        return model_id
    badge = " ✓Ücretsiz" if m["free"] else ""
    return f"{m['icon']} {m['display']}{badge}"


# ── Backward compat: eski "claude"/"gemini"/"glm" kısa isimlerini map et ──────

LEGACY_MAP = {
    "claude": "claude-opus-4-6",
    "gemini": "gemini-2.0-flash",
    "glm": "glm-4-plus",
}


def resolve_model_id(model: str) -> str:
    """Eski kısa isim veya tam model_id kabul eder, tam model_id döner."""
    if model in MODELS:
        return model
    return LEGACY_MAP.get(model, "claude-opus-4-6")
