"""
LangGraph Agent Tools
=====================
LangChain @tool dekoratörlü araçlar.
GraphAgent'ın code_gen node'u bu araçları yapılandırılmış çağrı olarak kullanır.
"""
import asyncio
import json
from typing import Optional
from langchain_core.tools import tool

from app.tools.file_tools import FileTools
from app.tools.search_tools import SearchTools
from app.tools.github_context import GitHubContextProvider

_file_tools = FileTools()
_search_tools = SearchTools()
_gh_context = GitHubContextProvider()


# ── GitHub Tools ──────────────────────────────────────────────────────────────

@tool
async def fetch_github_repo_context(repo: str) -> str:
    """
    GitHub reposundan kapsamlı bağlam çeker: README, teknoloji stack,
    açık issues, PR'lar ve son commitler.

    Args:
        repo: "owner/repo" formatında repo adı (örn: "tiangolo/fastapi")
    Returns:
        LLM'e enjekte edilmeye hazır bağlam metni
    """
    try:
        return await _gh_context.get_repo_context(repo)
    except Exception as e:
        return f"[GitHub bağlam hatası: {e}]"


@tool
async def fetch_github_file(repo: str, path: str) -> str:
    """
    GitHub reposundan belirli bir dosyanın içeriğini okur.

    Args:
        repo: "owner/repo" formatında repo adı
        path: Okunacak dosya yolu (örn: "src/main.py")
    Returns:
        Dosya içeriği
    """
    try:
        return await _gh_context.get_file_context(repo, path)
    except Exception as e:
        return f"[Dosya okuma hatası: {e}]"


@tool
async def search_github_repos(query: str) -> str:
    """
    GitHub'da repoları arar ve en popüler sonuçları döner.

    Args:
        query: Arama sorgusu (örn: "fastapi python rest api")
    Returns:
        Repo listesi (isim, açıklama, stars, URL)
    """
    try:
        return await _gh_context.search_repos(query)
    except Exception as e:
        return f"[GitHub arama hatası: {e}]"


@tool
async def search_github_code(query: str, repo: Optional[str] = None) -> str:
    """
    GitHub'da kod arar ve ilgili kod parçalarını döner.

    Args:
        query: Aranacak kod veya pattern
        repo: Opsiyonel: arama yapılacak repo ("owner/repo")
    Returns:
        Eşleşen kod örnekleri
    """
    try:
        return await _gh_context.search_code(query, repo)
    except Exception as e:
        return f"[Kod arama hatası: {e}]"


# ── File Tools ────────────────────────────────────────────────────────────────

@tool
async def read_project_file(path: str) -> str:
    """
    Proje workspace'indeki bir dosyayı okur.

    Args:
        path: Okunacak dosya yolu
    Returns:
        Dosya içeriği
    """
    try:
        return await _file_tools.read_file(path)
    except Exception as e:
        return f"[Dosya okuma hatası: {e}]"


@tool
async def write_project_file(path: str, content: str) -> str:
    """
    Proje workspace'ine dosya yazar veya günceller.

    Args:
        path: Yazılacak dosya yolu
        content: Dosya içeriği
    Returns:
        İşlem sonucu
    """
    try:
        await _file_tools.write_file(path, content)
        return f"✅ {path} başarıyla yazıldı."
    except Exception as e:
        return f"[Dosya yazma hatası: {e}]"


@tool
async def list_project_files(directory: str = ".") -> str:
    """
    Proje workspace'indeki dosya ve dizinleri listeler.

    Args:
        directory: Listenecek dizin (default: kök dizin)
    Returns:
        Dosya/dizin listesi
    """
    try:
        items = await _file_tools.list_files(directory)
        return json.dumps(items, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"[Dizin listeleme hatası: {e}]"


# ── Web Search ────────────────────────────────────────────────────────────────

@tool
async def search_web(query: str) -> str:
    """
    Web'de arama yapar; dokümantasyon, örnek kod ve çözümler bulur.

    Args:
        query: Arama sorgusu
    Returns:
        Arama sonuçları
    """
    try:
        results = await _search_tools.web_search(query)
        return _search_tools.format_search_results(results)
    except Exception as e:
        return f"[Web arama hatası: {e}]"


@tool
async def search_documentation(library: str, query: str) -> str:
    """
    Belirli bir kütüphanenin dokümantasyonunda arama yapar.

    Args:
        library: Kütüphane adı (örn: "fastapi", "react", "langchain")
        query: Dokümantasyonda aranacak konu
    Returns:
        İlgili doküman bölümleri
    """
    try:
        results = await _search_tools.search_docs(query, technology=library)
        return _search_tools.format_search_results(results)
    except Exception as e:
        return f"[Doküman arama hatası: {e}]"


# ── Tool Registry ─────────────────────────────────────────────────────────────

ALL_TOOLS = [
    fetch_github_repo_context,
    fetch_github_file,
    search_github_repos,
    search_github_code,
    read_project_file,
    write_project_file,
    list_project_files,
    search_web,
    search_documentation,
]

TOOL_MAP = {t.name: t for t in ALL_TOOLS}


def get_tool_schemas() -> list[dict]:
    """LLM'e sunulacak tool şemalarını döner."""
    schemas = []
    for t in ALL_TOOLS:
        schema = t.args_schema.model_json_schema() if t.args_schema else {}
        schemas.append({
            "name": t.name,
            "description": t.description,
            "parameters": schema,
        })
    return schemas


async def run_tool(tool_name: str, tool_args: dict) -> str:
    """Tool adı ve argümanlarıyla bir tool çalıştırır."""
    if tool_name not in TOOL_MAP:
        return f"[Bilinmeyen tool: {tool_name}]"
    t = TOOL_MAP[tool_name]
    try:
        result = await t.ainvoke(tool_args)
        return str(result)
    except Exception as e:
        return f"[Tool hatası ({tool_name}): {e}]"
