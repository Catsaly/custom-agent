"""
Planner Node
============
GitHub bağlamı da dahil ederek adım adım yürütme planı oluşturur.
"""
from app.ai.langgraph.state import AgentState
from app.ai.claude_client import ClaudeClient
from app.ai.gemini_client import GeminiClient
from app.ai.glm_client import GLMClient

_claude = ClaudeClient()
_gemini = GeminiClient()
_glm = GLMClient()

PLANNER_SYSTEM = """Sen bir uzman yazılım mimarısın.

Görevin: Kullanıcının isteğini ve varsa GitHub bağlamını analiz ederek
net, uygulanabilir bir yürütme planı oluşturmak.

Plan formatı:
## Yürütme Planı

### 1. Analiz
- ...

### 2. Tasarım
- ...

### 3. Uygulama
- Adım 3.1: ...
- Adım 3.2: ...

### 4. Test & Doğrulama
- ...

### Oluşturulacak Dosyalar
- `path/to/file.py` — açıklama
- ...

### Kullanılacak Teknolojiler
- ...

Planı Türkçe yaz. Spesifik, uygulanabilir ve detaylı ol.
"""


def _get_client(model: str):
    return {"claude": _claude, "gemini": _gemini, "glm": _glm}.get(model, _claude)


async def plan_node(state: AgentState) -> dict:
    """Görev için yürütme planı oluşturur."""
    task = state["task"]
    model = state.get("model", "claude")
    github_context = state.get("github_context")
    client = _get_client(model)

    # Kullanıcı mesajını hazırla
    content_parts = [f"## Görev\n{task}"]
    if github_context:
        content_parts.append(f"## GitHub Bağlamı\n{github_context}")
    content_parts.append("\nBu görev için detaylı bir yürütme planı oluştur.")

    messages = [{"role": "user", "content": "\n\n".join(content_parts)}]

    try:
        plan = await client.chat(messages, system=PLANNER_SYSTEM)
        return {
            "plan": plan,
            "current_node": "plan",
            "messages": [{"role": "system", "content": "[Plan] Yürütme planı oluşturuldu."}],
        }
    except Exception as e:
        # Plan başarısız olursa göreve devam et
        return {
            "plan": f"Plan: {task}",
            "current_node": "plan",
            "error": f"Planlama hatası: {e}",
        }
