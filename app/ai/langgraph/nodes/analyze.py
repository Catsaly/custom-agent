"""
Analyze Node
============
Görevi analiz eder: GitHub bağlamı gerekli mi, hangi repo, ne yapılacak?
"""
import json
import re
from app.ai.langgraph.state import AgentState
from app.ai.claude_client import ClaudeClient
from app.ai.gemini_client import GeminiClient
from app.ai.glm_client import GLMClient

_claude = ClaudeClient()
_gemini = GeminiClient()
_glm = GLMClient()

ANALYZE_SYSTEM = """Sen bir görev analiz uzmanısın.
Verilen görevi JSON formatında analiz et ve şu bilgileri çıkar:

1. needs_github: GitHub reposu gerekli mi? (true/false)
2. github_repo: Eğer GitHub repo gerekiyorsa "owner/repo" formatında (yoksa null)
3. github_file: Belirli bir dosya isteniyorsa yolu (yoksa null)
4. task_type: "code_generation" | "github_analysis" | "explanation" | "debugging" | "search"
5. complexity: "simple" | "medium" | "complex"
6. needs_plan: Detaylı plan gerekli mi? (true/false)
7. summary: Görevin tek cümle özeti (Türkçe)

SADECE JSON döndür, başka açıklama ekleme.

Örnek çıktı:
{
  "needs_github": true,
  "github_repo": "tiangolo/fastapi",
  "github_file": null,
  "task_type": "github_analysis",
  "complexity": "medium",
  "needs_plan": true,
  "summary": "FastAPI reposunu analiz et ve katkı kılavuzu hazırla"
}

GitHub repo tespiti için şunlara bak:
- "github.com/owner/repo" URL'leri
- "owner/repo" patternleri
- "X reposunu", "X projesini" gibi ifadeler
- Varsa token gibi kişisel repo referansları
"""


def _get_client(model: str):
    return {"claude": _claude, "gemini": _gemini, "glm": _glm}.get(model, _claude)


async def analyze_node(state: AgentState) -> dict:
    """Görevi analiz eder ve state'i günceller."""
    task = state["task"]
    model = state.get("model", "claude")
    client = _get_client(model)

    messages = [{"role": "user", "content": f"Analiz et:\n\n{task}"}]

    try:
        raw = await client.chat(messages, system=ANALYZE_SYSTEM)

        # JSON çıkar
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback: basit tahmin
            analysis = _fallback_analysis(task)

        # State güncellemesi
        updates = {
            "needs_github": analysis.get("needs_github", False),
            "github_repo": analysis.get("github_repo"),
            "github_file": analysis.get("github_file"),
            "current_node": "analyze",
            "messages": [{"role": "system", "content": f"[Analiz] {analysis.get('summary', task)}"}],
        }

        # Basit görevler için max_iter düşür
        complexity = analysis.get("complexity", "medium")
        if complexity == "simple":
            updates["max_iter"] = 1
        elif complexity == "complex":
            updates["max_iter"] = 3

        return updates

    except Exception as e:
        return {
            "needs_github": False,
            "github_repo": None,
            "github_file": None,
            "current_node": "analyze",
            "error": f"Analiz hatası: {e}",
            "messages": [{"role": "system", "content": f"[Analiz Hatası] {e}"}],
        }


def _fallback_analysis(task: str) -> dict:
    """LLM başarısız olursa kural tabanlı analiz."""
    task_lower = task.lower()

    # GitHub repo pattern tespiti
    repo_pattern = re.search(
        r"(?:github\.com/)?([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)", task
    )
    github_repo = repo_pattern.group(1) if repo_pattern else None
    needs_github = bool(
        github_repo
        or "github" in task_lower
        or "repo" in task_lower
        or "repository" in task_lower
    )

    return {
        "needs_github": needs_github,
        "github_repo": github_repo,
        "github_file": None,
        "task_type": "code_generation",
        "complexity": "medium",
        "needs_plan": True,
        "summary": task[:100],
    }
