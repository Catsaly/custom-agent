"""
GitHub Context Node
===================
GitHub API'den repo bağlamını çeker ve state'e ekler.
"""
from app.ai.langgraph.state import AgentState
from app.tools.github_context import GitHubContextProvider

_provider = GitHubContextProvider()


async def github_context_node(state: AgentState) -> dict:
    """GitHub bağlamını çeker ve state'i günceller."""
    repo = state.get("github_repo")
    file_path = state.get("github_file")

    if not repo:
        return {
            "github_context": None,
            "current_node": "github_context",
            "messages": [{"role": "system", "content": "[GitHub] Repo belirtilmedi, bağlam atlanıyor."}],
        }

    try:
        # Dosya belirtildiyse sadece onu çek, yoksa tam bağlamı
        if file_path:
            file_content = await _provider.get_file_context(repo, file_path)
            context = (
                f"## GitHub Dosyası: {repo}/{file_path}\n\n"
                f"```\n{file_content}\n```"
            )
        else:
            context = await _provider.get_repo_context(repo)

        return {
            "github_context": context,
            "current_node": "github_context",
            "messages": [{
                "role": "system",
                "content": f"[GitHub] `{repo}` reposundan bağlam çekildi ({len(context)} karakter).",
            }],
        }

    except Exception as e:
        error_msg = f"[GitHub] Bağlam çekme hatası ({repo}): {e}"
        return {
            "github_context": f"[GitHub bağlam çekilemedi: {e}]",
            "current_node": "github_context",
            "error": error_msg,
            "messages": [{"role": "system", "content": error_msg}],
        }
