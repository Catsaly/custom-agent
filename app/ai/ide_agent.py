"""
IDE Agent — Gerçek Tool Calling ile Akıllı Kodlama Ajanı
=========================================================
Claude (Anthropic) ve OpenAI-uyumlu modeller (Groq, OpenRouter) için
native tool calling kullanır. Her tool çağrısı SSE event olarak stream edilir.

Event formatı:
  {"type": "token",       "content": "..."}
  {"type": "tool_start",  "tool": "write_file", "input": {...}}
  {"type": "tool_result", "tool": "write_file", "output": "..."}
  {"type": "done",        "content": "..."}
  {"type": "error",       "content": "..."}
"""
import asyncio
import json
import os
import subprocess
import re
from pathlib import Path
from typing import AsyncIterator, Optional

import httpx

from app.ai.model_registry import get_model, resolve_model_id, MODELS
from app.config import settings

# ── Workspace Root ────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path("workspace")


def _abs(workspace_path: str, rel_path: str) -> Path:
    """Workspace içinde güvenli mutlak yol döner."""
    base = WORKSPACE_ROOT / workspace_path
    target = (base / rel_path).resolve()
    # Path traversal koruması
    if not str(target).startswith(str(base.resolve())):
        raise ValueError(f"Yol workspace dışına çıkıyor: {rel_path}")
    return target


# ── Tool Implementations ─────────────────────────────────────────────────────

async def _tool_read_file(path: str, workspace: str) -> str:
    try:
        target = _abs(workspace, path)
        if not target.exists():
            return f"HATA: Dosya bulunamadı: {path}"
        content = target.read_text(encoding="utf-8", errors="replace")
        return content or "(boş dosya)"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_write_file(path: str, content: str, workspace: str) -> str:
    try:
        target = _abs(workspace, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"✓ Dosya yazıldı: {path} ({len(content)} karakter)"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_delete_file(path: str, workspace: str) -> str:
    try:
        target = _abs(workspace, path)
        if not target.exists():
            return f"HATA: Dosya bulunamadı: {path}"
        target.unlink()
        return f"✓ Dosya silindi: {path}"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_list_files(directory: str, workspace: str) -> str:
    try:
        base = WORKSPACE_ROOT / workspace
        if directory and directory != "/" and directory != ".":
            base = _abs(workspace, directory)
        base.mkdir(parents=True, exist_ok=True)
        items = []
        for p in sorted(base.rglob("*")):
            if any(part.startswith(".") for part in p.parts):
                continue
            rel = p.relative_to(WORKSPACE_ROOT / workspace)
            prefix = "📁" if p.is_dir() else "📄"
            items.append(f"{prefix} {rel}")
        return "\n".join(items) if items else "(boş workspace)"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_run_command(command: str, workspace: str, timeout: int = 30) -> str:
    try:
        cwd = str(WORKSPACE_ROOT / workspace)
        os.makedirs(cwd, exist_ok=True)
        result = await asyncio.wait_for(
            asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
            ),
            timeout=timeout,
        )
        out = result.stdout[-3000:] if result.stdout else ""
        err = result.stderr[-1000:] if result.stderr else ""
        rc = result.returncode
        parts = [f"$ {command}", f"Exit code: {rc}"]
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        return "\n".join(parts)
    except asyncio.TimeoutError:
        return f"HATA: Komut zaman aşımına uğradı ({timeout}s): {command}"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            return results
        results = await asyncio.to_thread(_search)
        lines = []
        for r in results:
            lines.append(f"### {r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')[:300]}")
        return "\n\n".join(lines) or "Sonuç bulunamadı."
    except Exception as e:
        return f"HATA: {e}"


async def _tool_fetch_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            text = r.text[:8000]
            # HTML'den düz metin çıkar
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:5000] or "(boş sayfa)"
    except Exception as e:
        return f"HATA: {e}"


async def dispatch_tool(tool_name: str, tool_input: dict, workspace: str) -> str:
    """Tool adına göre doğru fonksiyonu çağırır."""
    if tool_name == "read_file":
        return await _tool_read_file(tool_input.get("path", ""), workspace)
    elif tool_name == "write_file":
        return await _tool_write_file(
            tool_input.get("path", ""), tool_input.get("content", ""), workspace
        )
    elif tool_name == "delete_file":
        return await _tool_delete_file(tool_input.get("path", ""), workspace)
    elif tool_name == "list_files":
        return await _tool_list_files(tool_input.get("directory", "."), workspace)
    elif tool_name == "run_command":
        return await _tool_run_command(
            tool_input.get("command", ""),
            workspace,
            tool_input.get("timeout", 30),
        )
    elif tool_name == "web_search":
        return await _tool_web_search(tool_input.get("query", ""))
    elif tool_name == "fetch_url":
        return await _tool_fetch_url(tool_input.get("url", ""))
    else:
        return f"HATA: Bilinmeyen tool: {tool_name}"


# ── Tool Schemas ─────────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Bir dosyanın içeriğini okur",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Workspace'e göre dosya yolu"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Dosya oluşturur veya günceller. Dizinleri otomatik oluşturur.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Dosya yolu"},
                "content": {"type": "string", "description": "Dosya içeriği"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "delete_file",
        "description": "Bir dosyayı siler",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Silinecek dosya yolu"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "Workspace'deki dosya ve klasörleri listeler",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Listelenecek dizin (varsayılan: kök)",
                }
            },
        },
    },
    {
        "name": "run_command",
        "description": "Shell komutu çalıştırır: pip install, npm install, python script.py, pytest vb.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Çalıştırılacak komut"},
                "timeout": {
                    "type": "integer",
                    "description": "Zaman aşımı (saniye, varsayılan: 30)",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "web_search",
        "description": "İnternet'te arama yapar — dokümantasyon, hata mesajları, kütüphane kullanımı için",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Arama sorgusu"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Bir URL'nin içeriğini çeker — dokümantasyon sayfaları için",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Okunacak URL"}
            },
            "required": ["url"],
        },
    },
]

# OpenAI-uyumlu format (Groq, OpenRouter için)
TOOL_SCHEMAS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
        },
    }
    for t in TOOL_SCHEMAS
]


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen gelişmiş bir AI kodlama asistanısın. Kullanıcının isteklerini yerine getirmek için araçlarını aktif olarak kullanırsın.

## Araçların:
- **read_file**: Dosya içeriğini oku
- **write_file**: Dosya oluştur veya güncelle (dizinler otomatik oluşturulur)
- **delete_file**: Dosya sil
- **list_files**: Dosyaları listele
- **run_command**: Komut çalıştır (pip install, npm install, pytest, python, vb.)
- **web_search**: Dokümantasyon ve çözüm ara
- **fetch_url**: URL içeriğini oku

## Kurallar:
1. İstek aldığında önce mevcut dosyaları incele (list_files, read_file)
2. Kod yaz ve dosyaları direkt oluştur (write_file) — açıklama bekletme
3. Paket gerekiyorsa hemen yükle (run_command: pip install ...)
4. Hata çözümünde önce hatayı oku, sonra dosyayı düzelt
5. Her işlemden sonra kısa bir Türkçe özet ver
6. Production-quality, eksiksiz kod yaz"""


# ── IDEAgent Class ────────────────────────────────────────────────────────────

class IDEAgent:
    """
    Tool calling ile çalışan IDE ajanı.
    Claude, Groq ve OpenRouter modellerini destekler.
    Her event SSE JSON formatında yield edilir.
    """

    async def run(
        self,
        messages: list[dict],
        model_id: str = "claude-opus-4-6",
        api_key: Optional[str] = None,
        workspace: str = "default",
    ) -> AsyncIterator[dict]:
        model_id = resolve_model_id(model_id)
        info = get_model(model_id)
        provider = info["provider"] if info else "anthropic"

        if provider == "anthropic":
            async for event in self._run_anthropic(messages, model_id, api_key, workspace):
                yield event
        elif provider in ("groq", "openrouter"):
            async for event in self._run_openai_compat(messages, model_id, api_key, provider, workspace):
                yield event
        elif provider == "gemini":
            async for event in self._run_gemini(messages, model_id, api_key, workspace):
                yield event
        else:
            # Fallback: GLM ve diğerleri — basit chat
            async for event in self._run_fallback(messages, model_id, api_key, workspace):
                yield event

    # ── Anthropic (Claude) ────────────────────────────────────────────────────

    async def _run_anthropic(
        self, messages: list[dict], model_id: str, api_key: Optional[str], workspace: str
    ) -> AsyncIterator[dict]:
        import anthropic
        key = api_key or settings.anthropic_api_key
        client = anthropic.AsyncAnthropic(api_key=key)

        msgs = [{"role": m["role"], "content": m["content"]} for m in messages
                if m.get("role") in ("user", "assistant")]

        for _ in range(10):  # max 10 tool-use döngüsü
            response = await client.messages.create(
                model=model_id,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=msgs,
            )

            # Text token'larını stream et
            text_parts = []
            tool_uses = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    # Token token yield et
                    for word in block.text.split(" "):
                        yield {"type": "token", "content": word + " "}
                elif block.type == "tool_use":
                    tool_uses.append(block)

            # Eğer tool yok → tamamlandı
            if not tool_uses:
                yield {"type": "done", "content": " ".join(text_parts)}
                return

            # Tool çağrılarını işle
            tool_results = []
            for tu in tool_uses:
                yield {"type": "tool_start", "tool": tu.name, "input": tu.input, "id": tu.id}
                output = await dispatch_tool(tu.name, tu.input, workspace)
                yield {"type": "tool_result", "tool": tu.name, "output": output, "id": tu.id}
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": output,
                })

            # Mesaj geçmişine ekle (döngü devam edecek)
            msgs.append({"role": "assistant", "content": response.content})
            msgs.append({"role": "user", "content": tool_results})

        yield {"type": "done", "content": ""}

    # ── OpenAI-uyumlu (Groq, OpenRouter) ─────────────────────────────────────

    async def _run_openai_compat(
        self, messages: list[dict], model_id: str, api_key: Optional[str],
        provider: str, workspace: str
    ) -> AsyncIterator[dict]:
        from openai import AsyncOpenAI

        if provider == "groq":
            base_url = "https://api.groq.com/openai/v1"
            key = api_key or settings.groq_api_key
        else:  # openrouter
            base_url = "https://openrouter.ai/api/v1"
            key = api_key or settings.openrouter_api_key

        client = AsyncOpenAI(api_key=key, base_url=base_url)
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                msgs.append({"role": m["role"], "content": m["content"]})

        for _ in range(10):
            response = await client.chat.completions.create(
                model=model_id,
                messages=msgs,
                tools=TOOL_SCHEMAS_OPENAI,
                tool_choice="auto",
                max_tokens=8192,
            )
            msg = response.choices[0].message
            content = msg.content or ""
            tool_calls = msg.tool_calls or []

            if content:
                for word in content.split(" "):
                    yield {"type": "token", "content": word + " "}

            if not tool_calls:
                yield {"type": "done", "content": content}
                return

            msgs.append({"role": "assistant", "content": content, "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls
            ]})

            for tc in tool_calls:
                try:
                    tool_input = json.loads(tc.function.arguments)
                except Exception:
                    tool_input = {}
                yield {"type": "tool_start", "tool": tc.function.name, "input": tool_input, "id": tc.id}
                output = await dispatch_tool(tc.function.name, tool_input, workspace)
                yield {"type": "tool_result", "tool": tc.function.name, "output": output, "id": tc.id}
                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": output,
                })

        yield {"type": "done", "content": ""}

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def _run_gemini(
        self, messages: list[dict], model_id: str, api_key: Optional[str], workspace: str
    ) -> AsyncIterator[dict]:
        import google.generativeai as genai

        key = api_key or settings.google_api_key
        if key:
            genai.configure(api_key=key)

        # Gemini function declarations
        from google.generativeai.types import FunctionDeclaration, Tool
        fn_decls = []
        for t in TOOL_SCHEMAS:
            props = {}
            for pname, pdef in t["input_schema"].get("properties", {}).items():
                props[pname] = {"type_": pdef.get("type", "string").upper(),
                                "description": pdef.get("description", "")}
            fn_decls.append(FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters={"type_": "OBJECT", "properties": props,
                            "required": t["input_schema"].get("required", [])},
            ))

        gemini_tools = Tool(function_declarations=fn_decls)
        model = genai.GenerativeModel(
            model_id,
            system_instruction=SYSTEM_PROMPT,
            tools=[gemini_tools],
        )
        chat = model.start_chat(history=[])

        # Convert messages
        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            chat.history.append({"role": role, "parts": [m["content"]]})

        last_msg = messages[-1]["content"]

        for _ in range(10):
            response = await asyncio.to_thread(chat.send_message, last_msg)
            part = response.candidates[0].content.parts[0]

            if hasattr(part, "text") and part.text:
                for word in part.text.split(" "):
                    yield {"type": "token", "content": word + " "}
                yield {"type": "done", "content": part.text}
                return

            if hasattr(part, "function_call"):
                fc = part.function_call
                tool_input = dict(fc.args)
                yield {"type": "tool_start", "tool": fc.name, "input": tool_input, "id": fc.name}
                output = await dispatch_tool(fc.name, tool_input, workspace)
                yield {"type": "tool_result", "tool": fc.name, "output": output, "id": fc.name}
                last_msg = output
            else:
                yield {"type": "done", "content": ""}
                return

        yield {"type": "done", "content": ""}

    # ── Fallback (GLM, diğerleri) ─────────────────────────────────────────────

    async def _run_fallback(
        self, messages: list[dict], model_id: str, api_key: Optional[str], workspace: str
    ) -> AsyncIterator[dict]:
        from app.ai.client_factory import get_client_for_model
        client = get_client_for_model(model_id, api_key=api_key)

        msgs = [{"role": m["role"], "content": m["content"]} for m in messages
                if m.get("role") in ("user", "assistant")]

        result = await client.chat(msgs, system=SYSTEM_PROMPT)
        for word in result.split(" "):
            yield {"type": "token", "content": word + " "}
        yield {"type": "done", "content": result}
