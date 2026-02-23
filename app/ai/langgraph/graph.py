"""
LangGraph Coding Agent — Grafik Montajı
========================================

Graf akışı:
  START
    │
    ▼
  analyze ──────────────────────────────────────────┐
    │                                                │
    │ needs_github=True                              │ needs_github=False
    ▼                                                │
  github_context                                     │
    │                                                │
    ▼                                                ▼
  plan ◄───────────────────────────────────────── plan
    │
    ▼
  code_gen
    │
    ▼
  review
    │
    │ passed=True or iteration>=max_iter
    ▼
  respond
    │
    ▼
  END

  review → code_gen (eğer passed=False ve iteration < max_iter)
"""
import uuid
from typing import AsyncIterator, Optional

from langgraph.graph import StateGraph, END, START

from app.ai.langgraph.state import AgentState
from app.ai.langgraph.nodes import (
    analyze_node,
    github_context_node,
    plan_node,
    code_gen_node,
    review_node,
    respond_node,
)
from app.ai.langgraph.nodes.coder import code_gen_stream


# ── Routing Functions ─────────────────────────────────────────────────────────

def route_after_analyze(state: AgentState) -> str:
    """Analiz sonrası: GitHub gerekli mi?"""
    if state.get("needs_github") and state.get("github_repo"):
        return "github_context"
    return "plan"


def route_after_review(state: AgentState) -> str:
    """İnceleme sonrası: tekrar kod üret mi yoksa bitir mi?"""
    passed = state.get("review_passed", True)
    iteration = state.get("iteration", 1)
    max_iter = state.get("max_iter", 2)

    if passed or iteration >= max_iter:
        return "respond"
    return "code_gen"


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """LangGraph graf yapısını oluşturur."""
    workflow = StateGraph(AgentState)

    # Node'ları kaydet
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("github_context", github_context_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("code_gen", code_gen_node)
    workflow.add_node("review", review_node)
    workflow.add_node("respond", respond_node)

    # Kenarlar
    workflow.add_edge(START, "analyze")
    workflow.add_conditional_edges(
        "analyze",
        route_after_analyze,
        {"github_context": "github_context", "plan": "plan"},
    )
    workflow.add_edge("github_context", "plan")
    workflow.add_edge("plan", "code_gen")
    workflow.add_edge("code_gen", "review")
    workflow.add_conditional_edges(
        "review",
        route_after_review,
        {"code_gen": "code_gen", "respond": "respond"},
    )
    workflow.add_edge("respond", END)

    return workflow


# ── GraphAgent ────────────────────────────────────────────────────────────────

class GraphAgent:
    """
    LangGraph tabanlı kodlama ajanı.
    Mevcut CodingAgent ile aynı arayüzü sağlar + graf yetkinlikleri ekler.
    """

    def __init__(self):
        graph = build_graph()
        self._app = graph.compile()

    def _make_initial_state(
        self,
        task: str,
        model: str = "claude",
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace_path: str = "workspace/default",
        github_repo: Optional[str] = None,
        max_iter: int = 2,
    ) -> AgentState:
        return {
            "messages": [],
            "task": task,
            "model": model,
            "needs_github": bool(github_repo),
            "github_repo": github_repo,
            "github_file": None,
            "github_context": None,
            "plan": None,
            "generated_files": {},
            "raw_response": None,
            "review_passed": False,
            "review_feedback": None,
            "iteration": 0,
            "max_iter": max_iter,
            "current_node": "start",
            "error": None,
            "final_answer": None,
            "session_id": session_id or str(uuid.uuid4()),
            "project_id": project_id,
            "workspace_path": workspace_path,
        }

    async def run(
        self,
        task: str,
        model: str = "claude",
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace_path: str = "workspace/default",
        github_repo: Optional[str] = None,
        max_iter: int = 2,
    ) -> AgentState:
        """Ajanı çalıştırır ve final state'i döner."""
        initial = self._make_initial_state(
            task=task,
            model=model,
            session_id=session_id,
            project_id=project_id,
            workspace_path=workspace_path,
            github_repo=github_repo,
            max_iter=max_iter,
        )
        config = {"recursion_limit": 20}
        final_state = await self._app.ainvoke(initial, config=config)
        return final_state

    async def stream_events(
        self,
        task: str,
        model: str = "claude",
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
        workspace_path: str = "workspace/default",
        github_repo: Optional[str] = None,
        max_iter: int = 2,
    ) -> AsyncIterator[dict]:
        """
        Graf olaylarını stream olarak döner.
        Her event: {"type": "node_start"|"node_end"|"message", "node": str, "data": ...}
        """
        initial = self._make_initial_state(
            task=task,
            model=model,
            session_id=session_id,
            project_id=project_id,
            workspace_path=workspace_path,
            github_repo=github_repo,
            max_iter=max_iter,
        )
        config = {"recursion_limit": 20}

        async for event in self._app.astream_events(initial, config=config, version="v2"):
            kind = event.get("event", "")
            node = event.get("name", "")

            if kind == "on_chain_start" and node in (
                "analyze", "github_context", "plan", "code_gen", "review", "respond"
            ):
                yield {"type": "node_start", "node": node, "data": None}

            elif kind == "on_chain_end" and node in (
                "analyze", "github_context", "plan", "code_gen", "review", "respond"
            ):
                output = event.get("data", {}).get("output", {})
                yield {
                    "type": "node_end",
                    "node": node,
                    "data": {
                        "messages": output.get("messages", []),
                        "generated_files": output.get("generated_files", {}),
                        "error": output.get("error"),
                    },
                }

            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", {})
                content = ""
                if hasattr(chunk, "content"):
                    content = chunk.content
                elif isinstance(chunk, dict):
                    content = chunk.get("content", "")
                if content:
                    yield {"type": "token", "node": node, "data": content}

    async def stream_code_gen(
        self,
        task: str,
        model: str = "claude",
        github_context: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Sadece kod üretim aşamasını stream eder (hafif mod).
        UI'da anlık token gösterimi için kullanılır.
        """
        partial_state: AgentState = {
            "messages": [],
            "task": task,
            "model": model,
            "needs_github": False,
            "github_repo": None,
            "github_file": None,
            "github_context": github_context,
            "plan": plan,
            "generated_files": {},
            "raw_response": None,
            "review_passed": False,
            "review_feedback": None,
            "iteration": 0,
            "max_iter": 1,
            "current_node": "code_gen",
            "error": None,
            "final_answer": None,
            "session_id": str(uuid.uuid4()),
            "project_id": None,
            "workspace_path": "workspace/default",
        }
        async for chunk in code_gen_stream(partial_state):
            yield chunk
