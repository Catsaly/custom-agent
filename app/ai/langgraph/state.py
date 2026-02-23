"""
LangGraph Agent State
=====================
Tüm node'lar arasında paylaşılan durum tanımı.
"""
from typing import TypedDict, Annotated, Optional, Dict, List, Any
import operator


def _add_messages(left: List[Dict], right: List[Dict]) -> List[Dict]:
    """İki mesaj listesini birleştirir (LangGraph reducer)."""
    return left + right


class AgentState(TypedDict):
    # ── Conversation ─────────────────────────────────────────────────────────
    messages: Annotated[List[Dict[str, str]], _add_messages]
    task: str
    model: str  # "claude" | "gemini" | "glm"

    # ── GitHub Context ───────────────────────────────────────────────────────
    needs_github: bool
    github_repo: Optional[str]   # "owner/repo" formatında
    github_file: Optional[str]   # İstenen dosya yolu (opsiyonel)
    github_context: Optional[str]  # Format edilmiş bağlam metni (LLM'e inject edilir)

    # ── Execution Plan ───────────────────────────────────────────────────────
    plan: Optional[str]          # LLM'in oluşturduğu adım adım plan

    # ── Code Generation ──────────────────────────────────────────────────────
    generated_files: Dict[str, str]   # {path: content}
    raw_response: Optional[str]       # LLM'in ham çıktısı

    # ── Review ───────────────────────────────────────────────────────────────
    review_passed: bool
    review_feedback: Optional[str]

    # ── Control Flow ─────────────────────────────────────────────────────────
    iteration: int       # Kaçıncı code-gen döngüsündeyiz
    max_iter: int        # Maksimum yeniden deneme sayısı
    current_node: str    # Debug için hangi node'dayız
    error: Optional[str]

    # ── Output ───────────────────────────────────────────────────────────────
    final_answer: Optional[str]

    # ── Session ──────────────────────────────────────────────────────────────
    session_id: str
    project_id: Optional[str]
    workspace_path: str
