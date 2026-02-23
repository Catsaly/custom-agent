"""
Responder Node
==============
Son yanıtı formatlayıp kullanıcıya sunar.
"""
from app.ai.langgraph.state import AgentState


def respond_node(state: AgentState) -> dict:
    """Ham çıktıyı kullanıcıya sunulmak üzere formatlar."""
    raw = state.get("raw_response", "")
    generated_files = state.get("generated_files", {})
    github_repo = state.get("github_repo")
    github_context = state.get("github_context")
    plan = state.get("plan")
    iteration = state.get("iteration", 1)
    error = state.get("error")

    sections = []

    # GitHub bağlamı kullanıldıysa belirt
    if github_context and github_repo:
        sections.append(f"> **GitHub Bağlamı:** `{github_repo}` reposundan veri çekildi.")

    # Hata varsa göster
    if error and not raw:
        sections.append(f"⚠️ **Hata:** {error}")
        final = "\n\n".join(sections)
        return {
            "final_answer": final,
            "current_node": "respond",
            "messages": [{"role": "assistant", "content": final}],
        }

    # Ana yanıt
    if raw:
        sections.append(raw)

    # Üretilen dosyaların özeti
    if generated_files:
        file_list = "\n".join(f"- `{path}`" for path in generated_files.keys())
        sections.append(f"\n---\n**Oluşturulan Dosyalar ({len(generated_files)}):**\n{file_list}")

    # İterasyon bilgisi
    if iteration > 1:
        sections.append(f"\n> *{iteration} iterasyonda tamamlandı.*")

    final = "\n\n".join(s for s in sections if s)

    return {
        "final_answer": final,
        "current_node": "respond",
        "messages": [{"role": "assistant", "content": final}],
    }
