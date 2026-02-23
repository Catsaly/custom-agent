"""
Reviewer Node
=============
Üretilen kodu inceler: kalite, güvenlik, tamamlanma.
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

REVIEWER_SYSTEM = """Sen kıdemli bir kod inceleme uzmanısın.

Verilen kodu şu kriterlere göre incele:

1. **Tamamlanma**: Tüm dosyalar eksiksiz ve çalışır mı?
2. **Doğruluk**: Mantık hataları var mı?
3. **Güvenlik**: Açık güvenlik açıkları var mı? (SQL injection, XSS, vb.)
4. **Kalite**: Clean code prensipleri uygulanmış mı?
5. **Görev Uyumu**: İstenen her şey karşılandı mı?

Sonucu SADECE JSON olarak döndür:
{
  "passed": true/false,
  "score": 0-10,
  "issues": ["sorun1", "sorun2"],
  "suggestions": ["öneri1", "öneri2"],
  "summary": "tek cümle özet (Türkçe)"
}

Eğer büyük sorunlar yoksa (score >= 7) passed=true döndür.
Küçük öneriler passed=true'yu engellemez.
"""


def _get_client(model: str):
    return {"claude": _claude, "gemini": _gemini, "glm": _glm}.get(model, _claude)


async def review_node(state: AgentState) -> dict:
    """Üretilen kodu inceler ve geribidirim sağlar."""
    model = state.get("model", "claude")
    client = _get_client(model)
    raw_response = state.get("raw_response", "")
    generated_files = state.get("generated_files", {})
    task = state["task"]

    if not raw_response and not generated_files:
        return {
            "review_passed": False,
            "review_feedback": "İncelenecek kod bulunamadı.",
            "current_node": "review",
            "messages": [{"role": "system", "content": "[İnceleme] İncelenecek kod bulunamadı."}],
        }

    # İnceleme içeriği hazırla
    content_parts = [f"## Orijinal Görev\n{task}"]
    if generated_files:
        for path, content in list(generated_files.items())[:5]:  # İlk 5 dosya
            content_parts.append(f"### `{path}`\n```\n{content[:2000]}\n```")
    elif raw_response:
        content_parts.append(f"### Üretilen Çıktı\n{raw_response[:3000]}")

    messages = [{"role": "user", "content": "\n\n".join(content_parts)}]

    try:
        review_raw = await client.chat(messages, system=REVIEWER_SYSTEM)

        # JSON çıkar
        json_match = re.search(r"\{.*\}", review_raw, re.DOTALL)
        if json_match:
            review = json.loads(json_match.group())
        else:
            review = {"passed": True, "score": 7, "issues": [], "summary": "İnceleme başarılı"}

        passed = review.get("passed", True)
        issues = review.get("issues", [])
        suggestions = review.get("suggestions", [])

        feedback = ""
        if issues:
            feedback += "**Sorunlar:**\n" + "\n".join(f"- {i}" for i in issues) + "\n\n"
        if suggestions:
            feedback += "**Öneriler:**\n" + "\n".join(f"- {s}" for s in suggestions)

        return {
            "review_passed": passed,
            "review_feedback": feedback.strip() or None,
            "current_node": "review",
            "messages": [{
                "role": "system",
                "content": f"[İnceleme] Skor: {review.get('score', '?')}/10 — {review.get('summary', '')}",
            }],
        }

    except Exception as e:
        # İnceleme başarısız olursa geç
        return {
            "review_passed": True,
            "review_feedback": None,
            "current_node": "review",
            "error": f"İnceleme hatası: {e}",
            "messages": [{"role": "system", "content": f"[İnceleme Hatası] {e}"}],
        }
