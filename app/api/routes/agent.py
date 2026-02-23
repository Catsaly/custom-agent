"""
LangGraph Agent API Routes
===========================
/api/agent/* endpointleri — LangGraph tabanlı ajan çalıştırma.
"""
import json
import uuid
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.langgraph import GraphAgent
from app.tools.github_context import GitHubContextProvider

router = APIRouter(prefix="/agent", tags=["LangGraph Agent"])

# Singleton'lar (başlatma maliyetli değil ama tutarlı)
_graph_agent = GraphAgent()
_gh_context = GitHubContextProvider()


# ── Request / Response Models ─────────────────────────────────────────────────

class AgentRunRequest(BaseModel):
    task: str
    model: Literal["claude", "gemini", "glm"] = "claude"
    github_repo: Optional[str] = None   # "owner/repo"
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_path: str = "workspace/default"
    max_iter: int = 2


class AgentStreamRequest(BaseModel):
    task: str
    model: Literal["claude", "gemini", "glm"] = "claude"
    github_repo: Optional[str] = None
    session_id: Optional[str] = None
    workspace_path: str = "workspace/default"
    max_iter: int = 2


class GitHubContextRequest(BaseModel):
    repo: str                             # "owner/repo"
    include_issues: bool = True
    include_prs: bool = True
    include_commits: bool = True


class GitHubFileRequest(BaseModel):
    repo: str
    path: str
    branch: str = "main"


class GitHubSearchRequest(BaseModel):
    query: str
    limit: int = 5


class GitHubCodeSearchRequest(BaseModel):
    query: str
    repo: Optional[str] = None
    limit: int = 5


# ── Agent Endpoints ───────────────────────────────────────────────────────────

@router.post("/run")
async def run_agent(req: AgentRunRequest):
    """
    LangGraph ajanını çalıştırır ve tamamlanmış sonucu döner.

    Graf akışı: analyze → [github_context] → plan → code_gen → review → respond
    """
    try:
        final_state = await _graph_agent.run(
            task=req.task,
            model=req.model,
            github_repo=req.github_repo,
            session_id=req.session_id or str(uuid.uuid4()),
            project_id=req.project_id,
            workspace_path=req.workspace_path,
            max_iter=req.max_iter,
        )
        return {
            "final_answer": final_state.get("final_answer"),
            "generated_files": final_state.get("generated_files", {}),
            "plan": final_state.get("plan"),
            "github_context_used": bool(final_state.get("github_context")),
            "github_repo": final_state.get("github_repo"),
            "iteration": final_state.get("iteration", 1),
            "review_passed": final_state.get("review_passed", True),
            "error": final_state.get("error"),
            "session_id": final_state.get("session_id"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_agent(req: AgentStreamRequest):
    """
    LangGraph ajan olaylarını Server-Sent Events (SSE) olarak stream eder.

    Event tipleri:
    - node_start: Bir node çalışmaya başladı
    - node_end: Bir node tamamlandı
    - token: LLM token çıktısı
    - done: Graf tamamlandı
    - error: Hata oluştu
    """
    async def event_generator():
        try:
            async for event in _graph_agent.stream_events(
                task=req.task,
                model=req.model,
                github_repo=req.github_repo,
                session_id=req.session_id or str(uuid.uuid4()),
                workspace_path=req.workspace_path,
                max_iter=req.max_iter,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/stream-code")
async def stream_code_only(req: AgentStreamRequest):
    """
    Sadece kod üretim aşamasını stream eder (hafif mod, GitHub bağlam olmadan).
    UI'da anlık yazım efekti için kullanılır.
    """
    async def token_generator():
        try:
            async for chunk in _graph_agent.stream_code_gen(
                task=req.task,
                model=req.model,
            ):
                if chunk:
                    yield chunk
        except Exception as e:
            yield f"\n[Hata: {e}]"

    return StreamingResponse(token_generator(), media_type="text/plain")


# ── GitHub Context Endpoints ──────────────────────────────────────────────────

@router.post("/github/context")
async def get_github_context(req: GitHubContextRequest):
    """
    GitHub reposundan kapsamlı bağlam çeker.
    Bu bağlam /agent/run endpoint'ine 'github_repo' parametresiyle iletilir
    veya doğrudan LLM sistem promptuna eklenebilir.
    """
    try:
        context = await _gh_context.get_repo_context(
            repo_name=req.repo,
            include_issues=req.include_issues,
            include_prs=req.include_prs,
            include_commits=req.include_commits,
        )
        return {
            "repo": req.repo,
            "context": context,
            "length": len(context),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GitHub bağlam hatası: {e}")


@router.post("/github/file")
async def get_github_file(req: GitHubFileRequest):
    """Belirli bir GitHub dosyasının içeriğini döner."""
    try:
        content = await _gh_context.get_file_context(req.repo, req.path, req.branch)
        return {"repo": req.repo, "path": req.path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya okuma hatası: {e}")


@router.get("/github/search-repos")
async def search_github_repos(q: str, limit: int = 5):
    """GitHub'da repoları arar."""
    try:
        results = await _gh_context.search_repos(q, limit)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/github/search-code")
async def search_github_code(q: str, repo: Optional[str] = None, limit: int = 5):
    """GitHub'da kod arar."""
    try:
        results = await _gh_context.search_code(q, repo, limit)
        return {"query": q, "repo": repo, "results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/github/analyze-for-task")
async def analyze_repo_for_task(repo: str, task: str, model: str = "claude"):
    """
    Bir repoyu belirli bir görev için analiz eder ve
    LangGraph ajanını o bağlamla çalıştırır.

    Örnek: repo="tiangolo/fastapi", task="authentication middleware ekle"
    """
    try:
        final_state = await _graph_agent.run(
            task=task,
            model=model,
            github_repo=repo,
            max_iter=2,
        )
        return {
            "repo": repo,
            "task": task,
            "final_answer": final_state.get("final_answer"),
            "generated_files": final_state.get("generated_files", {}),
            "plan": final_state.get("plan"),
            "error": final_state.get("error"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
