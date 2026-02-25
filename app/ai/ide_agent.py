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
    if not str(target).startswith(str(base.resolve())):
        raise ValueError(f"Yol workspace dışına çıkıyor: {rel_path}")
    return target


# ── Tool Implementations ──────────────────────────────────────────────────────

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
        lines = content.count("\n") + 1
        return f"✓ Dosya yazıldı: {path} ({len(content)} karakter, {lines} satır)"
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
        if directory and directory not in ("/", "."):
            base = _abs(workspace, directory)
        base.mkdir(parents=True, exist_ok=True)
        items = []
        for p in sorted(base.rglob("*")):
            if any(part.startswith(".") for part in p.parts):
                continue
            rel = p.relative_to(WORKSPACE_ROOT / workspace)
            prefix = "📁" if p.is_dir() else "📄"
            size = f" ({p.stat().st_size}B)" if p.is_file() else ""
            items.append(f"{prefix} {rel}{size}")
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
        return f"HATA: Zaman aşımı ({timeout}s): {command}"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_web_search(query: str) -> str:
    try:
        from duckduckgo_search import DDGS
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=6))
        results = await asyncio.to_thread(_search)
        lines = []
        for r in results:
            lines.append(f"### {r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')[:400]}")
        return "\n\n".join(lines) or "Sonuç bulunamadı."
    except Exception as e:
        return f"HATA: {e}"


async def _tool_fetch_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            text = r.text[:8000]
            text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
            text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:5000] or "(boş sayfa)"
    except Exception as e:
        return f"HATA: {e}"


# ── NEW TOOLS ─────────────────────────────────────────────────────────────────

async def _tool_search_files(pattern: str, workspace: str, path: str = "",
                              case_sensitive: bool = False) -> str:
    """Workspace dosyalarında metin/regex araması (grep benzeri)."""
    try:
        base = WORKSPACE_ROOT / workspace
        if path:
            base = _abs(workspace, path)
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error:
            regex = re.compile(re.escape(pattern), flags)

        for file_path in sorted(base.rglob("*")):
            if not file_path.is_file():
                continue
            if any(part.startswith(".") for part in file_path.parts):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        rel = file_path.relative_to(WORKSPACE_ROOT / workspace)
                        results.append(f"{rel}:{i}: {line.strip()}")
                        if len(results) >= 40:
                            results.append("... (ilk 40 sonuç gösterildi)")
                            return "\n".join(results)
            except Exception:
                pass
        return "\n".join(results) if results else f"'{pattern}' için eşleşme bulunamadı."
    except Exception as e:
        return f"HATA: {e}"


async def _tool_rename_file(old_path: str, new_path: str, workspace: str) -> str:
    """Dosya veya dizini yeniden adlandırır / taşır."""
    try:
        src = _abs(workspace, old_path)
        dst = _abs(workspace, new_path)
        if not src.exists():
            return f"HATA: Kaynak bulunamadı: {old_path}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"✓ Taşındı: {old_path} → {new_path}"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_create_directory(path: str, workspace: str) -> str:
    """Dizin(ler) oluşturur (mkdir -p)."""
    try:
        target = _abs(workspace, path)
        target.mkdir(parents=True, exist_ok=True)
        return f"✓ Dizin oluşturuldu: {path}"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_patch_file(path: str, old_text: str, new_text: str,
                            workspace: str) -> str:
    """Dosyadaki belirli bir metni değiştirir. Tüm dosyayı yeniden yazmak yerine
    cerrahi değişiklik için kullan."""
    try:
        target = _abs(workspace, path)
        if not target.exists():
            return f"HATA: Dosya bulunamadı: {path}"
        content = target.read_text(encoding="utf-8", errors="replace")
        if old_text not in content:
            return f"HATA: Değiştirilecek metin dosyada bulunamadı:\n{old_text[:200]}"
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text)
        target.write_text(new_content, encoding="utf-8")
        return f"✓ Değiştirildi: {path} ({count} adet)"
    except Exception as e:
        return f"HATA: {e}"


async def _tool_git_command(command: str, workspace: str) -> str:
    """Git komutu çalıştırır. Örnek: git status, git log --oneline -10,
    git diff, git add ., git commit -m 'msg'"""
    # Güvenli git komutları — yıkıcı olanlar engellenir
    blocked = ["push --force", "reset --hard", "clean -f", "branch -D"]
    for b in blocked:
        if b in command:
            return f"HATA: Yıkıcı git komutu engellendi: {b}"
    if not command.strip().startswith("git "):
        command = "git " + command
    return await _tool_run_command(command, workspace, timeout=15)


async def _tool_run_tests(workspace: str, command: str = "") -> str:
    """Test çalıştırır. Komut belirtilmezse otomatik algılar:
    pytest, npm test, cargo test, go test"""
    if command:
        return await _tool_run_command(command, workspace, timeout=60)
    # Otomatik algıla
    cwd = Path(WORKSPACE_ROOT / workspace)
    if (cwd / "pytest.ini").exists() or (cwd / "pyproject.toml").exists() or list(cwd.rglob("test_*.py")):
        return await _tool_run_command("python -m pytest -v --tb=short 2>&1 | tail -40", workspace, timeout=60)
    if (cwd / "package.json").exists():
        return await _tool_run_command("npm test -- --passWithNoTests 2>&1 | tail -40", workspace, timeout=60)
    if (cwd / "Cargo.toml").exists():
        return await _tool_run_command("cargo test 2>&1 | tail -40", workspace, timeout=60)
    if list(cwd.rglob("*_test.go")):
        return await _tool_run_command("go test ./... 2>&1 | tail -40", workspace, timeout=60)
    return "Test dosyası bulunamadı. Hangi test komutu kullanmak istediğinizi belirtin."


async def _tool_append_to_file(path: str, content: str, workspace: str) -> str:
    """Dosyanın sonuna içerik ekler (mevcut içeriği silmez)."""
    try:
        target = _abs(workspace, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"✓ Eklendi: {path} (+{len(content)} karakter)"
    except Exception as e:
        return f"HATA: {e}"


async def dispatch_tool(tool_name: str, tool_input: dict, workspace: str) -> str:
    """Tool adına göre doğru fonksiyonu çağırır."""
    match tool_name:
        case "read_file":
            return await _tool_read_file(tool_input.get("path", ""), workspace)
        case "write_file":
            return await _tool_write_file(
                tool_input.get("path", ""), tool_input.get("content", ""), workspace)
        case "delete_file":
            return await _tool_delete_file(tool_input.get("path", ""), workspace)
        case "list_files":
            return await _tool_list_files(tool_input.get("directory", "."), workspace)
        case "run_command":
            return await _tool_run_command(
                tool_input.get("command", ""), workspace, tool_input.get("timeout", 30))
        case "web_search":
            return await _tool_web_search(tool_input.get("query", ""))
        case "fetch_url":
            return await _tool_fetch_url(tool_input.get("url", ""))
        case "search_files":
            return await _tool_search_files(
                tool_input.get("pattern", ""), workspace,
                tool_input.get("path", ""),
                tool_input.get("case_sensitive", False))
        case "rename_file":
            return await _tool_rename_file(
                tool_input.get("old_path", ""), tool_input.get("new_path", ""), workspace)
        case "create_directory":
            return await _tool_create_directory(tool_input.get("path", ""), workspace)
        case "patch_file":
            return await _tool_patch_file(
                tool_input.get("path", ""), tool_input.get("old_text", ""),
                tool_input.get("new_text", ""), workspace)
        case "git_command":
            return await _tool_git_command(tool_input.get("command", ""), workspace)
        case "run_tests":
            return await _tool_run_tests(workspace, tool_input.get("command", ""))
        case "append_to_file":
            return await _tool_append_to_file(
                tool_input.get("path", ""), tool_input.get("content", ""), workspace)
        case _:
            return f"HATA: Bilinmeyen tool: {tool_name}"


# ── Tool Schemas ──────────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Bir dosyanın içeriğini okur",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Workspace'e göre dosya yolu"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Dosya oluşturur veya tamamen yeniden yazar. Dizinleri otomatik oluşturur. "
                       "Küçük değişiklikler için patch_file tercih et.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Dosya yolu"},
                "content": {"type": "string", "description": "Tam dosya içeriği"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "patch_file",
        "description": "Dosyadaki belirli bir metni değiştirir — tüm dosyayı yeniden yazmak yerine "
                       "cerrahi düzenleme için kullan (bug fix, refactor, satır değiştirme)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Dosya yolu"},
                "old_text": {"type": "string", "description": "Değiştirilecek mevcut metin (tam eşleşme)"},
                "new_text": {"type": "string", "description": "Yeni metin"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "append_to_file",
        "description": "Dosyanın sonuna içerik ekler (log, not, satır ekleme için)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Dosya yolu"},
                "content": {"type": "string", "description": "Eklenecek içerik"},
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
                "path": {"type": "string", "description": "Silinecek dosya yolu"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "rename_file",
        "description": "Dosya veya dizini yeniden adlandırır ya da taşır",
        "input_schema": {
            "type": "object",
            "properties": {
                "old_path": {"type": "string", "description": "Mevcut dosya/dizin yolu"},
                "new_path": {"type": "string", "description": "Yeni dosya/dizin yolu"},
            },
            "required": ["old_path", "new_path"],
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
                },
            },
        },
    },
    {
        "name": "create_directory",
        "description": "Dizin oluşturur (mkdir -p gibi, iç içe dizinler dahil)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Oluşturulacak dizin yolu"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_files",
        "description": "Workspace dosyalarında metin veya regex araması yapar (grep benzeri). "
                       "Belirli bir fonksiyon, değişken, hata mesajı aramak için kullan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Aranacak metin veya regex"},
                "path": {"type": "string", "description": "Arama yapılacak alt dizin (opsiyonel)"},
                "case_sensitive": {"type": "boolean", "description": "Büyük/küçük harf duyarlı (varsayılan: false)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_command",
        "description": "Shell komutu çalıştırır: pip install, npm install, python script.py, vb.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Çalıştırılacak komut"},
                "timeout": {"type": "integer", "description": "Zaman aşımı saniye (varsayılan: 30)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "run_tests",
        "description": "Testleri çalıştırır. Komut belirtilmezse pytest/npm test/cargo test otomatik algılanır.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Test komutu (boş bırakılırsa otomatik algılanır)",
                },
            },
        },
    },
    {
        "name": "git_command",
        "description": "Git komutları çalıştırır: git status, git log, git diff, git add, git commit, git branch",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Git komutu (git ile başlaması gerekmez). Örn: 'status', 'log --oneline -10', 'diff'",
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
                "query": {"type": "string", "description": "Arama sorgusu"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Bir URL'nin içeriğini çeker — dokümantasyon, README, API dökümanı için",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Okunacak URL"},
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

SYSTEM_PROMPT = """Sen gelişmiş bir AI kodlama asistanısın. Her görevi en uygun araç seçimiyle çözersin.

## Araçların (14 adet):

### Dosya İşlemleri
- **read_file** — dosya oku
- **write_file** — dosya oluştur veya tümünü yeniden yaz
- **patch_file** — dosyada belirli bir metni değiştir (cerrahi düzenleme — write_file'a tercih et)
- **append_to_file** — dosyanın sonuna ekle
- **delete_file** — dosya sil
- **rename_file** — dosya/dizin taşı veya yeniden adlandır
- **list_files** — dosya listele
- **create_directory** — dizin oluştur
- **search_files** — dosya içinde metin/regex ara (grep)

### Komut & Test
- **run_command** — shell komutu çalıştır (pip install, npm, python, vb.)
- **run_tests** — testleri çalıştır (pytest/npm test/cargo test otomatik algılanır)
- **git_command** — git işlemleri (status, log, diff, add, commit)

### Web & Araştırma
- **web_search** — internet araması
- **fetch_url** — URL içeriğini oku

## Görev Tipine Göre Yaklaşım Stratejileri:

### 🆕 Yeni proje / özellik ekle
1. list_files → mevcut yapıyı anla
2. create_directory → gerekli dizinleri oluştur
3. write_file → dosyaları yaz (önce ana modül, sonra yardımcılar)
4. run_command → bağımlılıkları yükle
5. run_tests → doğrula

### 🐛 Hata ayıklama
1. read_file → hatalı dosyayı oku
2. search_files → hatayı veya ilgili kodu bul
3. patch_file → cerrahi düzeltme yap (tüm dosyayı yeniden yazma)
4. run_command → test et

### ♻️ Refactoring
1. search_files → değiştirilecek tüm kullanımları bul
2. patch_file → her dosyada cerrahi değişiklik
3. run_tests → regresyon kontrolü

### 🔬 Araştırma gerektiren görev
1. web_search → çözüm/dokümantasyon ara
2. fetch_url → ilgili sayfayı oku
3. write_file veya patch_file → çözümü uygula

### 📦 Dosyadan analiz / işlem (ekteki dosya)
1. Eklenen dosyayı doğrudan kullan — ayrıca okumana gerek yok
2. Gerekirse write_file ile sonucu kaydet

### 🔀 Git işlemleri
1. git_command status → durum kontrol
2. git_command diff → değişikliklere bak
3. git_command add + commit → kaydet

## Kurallar:
- Küçük değişiklikler için write_file yerine **patch_file** kullan
- Arama gerekirken önce **search_files** ile bul, sonra düzenle
- Paket gerekirken hemen **run_command** ile yükle
- Her işlem sonrası kısa Türkçe özet ver
- Production-quality, eksiksiz kod yaz
- Ek dosya içeriği mesajda `📎` ile başlıyorsa, onu direkt kullan"""


# ── IDEAgent Class ────────────────────────────────────────────────────────────

class IDEAgent:
    """
    Tool calling ile çalışan IDE ajanı.
    Claude, Groq, OpenRouter ve Gemini modellerini destekler.
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

        for _ in range(12):
            response = await client.messages.create(
                model=model_id,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                tools=TOOL_SCHEMAS,
                messages=msgs,
            )

            text_parts = []
            tool_uses = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
                    for word in block.text.split(" "):
                        yield {"type": "token", "content": word + " "}
                elif block.type == "tool_use":
                    tool_uses.append(block)

            if not tool_uses:
                yield {"type": "done", "content": " ".join(text_parts)}
                return

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
        else:
            base_url = "https://openrouter.ai/api/v1"
            key = api_key or settings.openrouter_api_key

        client = AsyncOpenAI(api_key=key, base_url=base_url)
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                msgs.append({"role": m["role"], "content": m["content"]})

        for _ in range(12):
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

        from google.generativeai.types import FunctionDeclaration, Tool
        fn_decls = []
        for t in TOOL_SCHEMAS:
            props = {}
            for pname, pdef in t["input_schema"].get("properties", {}).items():
                ptype = pdef.get("type", "string")
                gemini_type = {"string": "STRING", "integer": "INTEGER",
                               "boolean": "BOOLEAN", "number": "NUMBER"}.get(ptype, "STRING")
                props[pname] = {"type_": gemini_type, "description": pdef.get("description", "")}
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

        for m in messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            chat.history.append({"role": role, "parts": [m["content"]]})

        last_msg = messages[-1]["content"]

        for _ in range(12):
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
