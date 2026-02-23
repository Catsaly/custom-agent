"""
Code Generation Node
====================
Plan ve GitHub bağlamını kullanarak kod üretir.
Tool calling döngüsü ile web araması ve dosya okuma yapabilir.
"""
import json
import re
from typing import AsyncIterator
from app.ai.langgraph.state import AgentState
from app.ai.claude_client import ClaudeClient
from app.ai.gemini_client import GeminiClient
from app.ai.glm_client import GLMClient
from app.ai.langgraph.tools import run_tool, get_tool_schemas
from app.tools.file_tools import FileTools

_claude = ClaudeClient()
_gemini = GeminiClient()
_glm = GLMClient()
_file_tools = FileTools()

MAX_TOOL_CALLS = 4  # Tek turda maksimum tool çağrısı

CODER_SYSTEM = """Sen Milli Yapay Zeka platformunun uzman yazılım geliştirici motorusun.

Görevin: Verilen plan ve GitHub bağlamını kullanarak eksiksiz, production-ready kod üretmek.

## Kurallar
1. Tam ve çalışan kod yaz — parça veya taslak değil
2. Modern best practice'leri kullan
3. Her dosyayı şu formatla işaretle:
   <FILE path="tam/yol/dosya.uzantisi">
   dosya içeriği
   </FILE>
4. Türkçe açıklama ekle; kod içi yorumlar İngilizce olabilir
5. Dosya oluşturduktan sonra özet sun
6. Hata ayıklama isteklerinde tam düzeltilmiş kodu ver

## Tool Kullanımı
Eğer bilgi gerekiyorsa şu formatla tool çağır:
<TOOL_CALL>
{"tool": "tool_adı", "args": {"parametre": "değer"}}
</TOOL_CALL>

Mevcut tool'lar:
{tool_schemas}

## GitHub Bağlamı
GitHub bağlamı varsa:
- Mevcut teknoloji stack'ini kullan
- Mevcut dosya yapısına uyu
- Var olan pattern ve stil kurallarını takip et
- Açık issues/PR'ları göz önünde bulundur
"""


def _get_client(model: str):
    return {"claude": _claude, "gemini": _gemini, "glm": _glm}.get(model, _claude)


def _build_system_prompt() -> str:
    tool_schemas = json.dumps(get_tool_schemas(), ensure_ascii=False, indent=2)
    return CODER_SYSTEM.format(tool_schemas=tool_schemas)


def _build_user_message(state: AgentState) -> str:
    parts = [f"## Görev\n{state['task']}"]

    if state.get("plan"):
        parts.append(f"## Yürütme Planı\n{state['plan']}")

    if state.get("github_context"):
        parts.append(f"## GitHub Bağlamı\n{state['github_context']}")

    if state.get("review_feedback") and state.get("iteration", 0) > 0:
        parts.append(
            f"## İnceleme Geri Bildirimi (İterasyon {state['iteration']})\n"
            f"{state['review_feedback']}\n\n"
            "Lütfen bu sorunları düzelt."
        )

    return "\n\n---\n\n".join(parts)


async def _process_tool_calls(response: str) -> tuple[str, list[str]]:
    """Tool çağrılarını tespit eder, çalıştırır ve sonuçları döner."""
    tool_results = []
    calls_found = re.findall(r"<TOOL_CALL>(.*?)</TOOL_CALL>", response, re.DOTALL)

    for call_json in calls_found[:MAX_TOOL_CALLS]:
        try:
            call = json.loads(call_json.strip())
            tool_name = call.get("tool", "")
            tool_args = call.get("args", {})
            result = await run_tool(tool_name, tool_args)
            tool_results.append(f"[Tool: {tool_name}]\n{result}")
        except Exception as e:
            tool_results.append(f"[Tool hatası: {e}]")

    # Tool call bloklarını temizle
    clean_response = re.sub(r"<TOOL_CALL>.*?</TOOL_CALL>", "", response, flags=re.DOTALL).strip()
    return clean_response, tool_results


async def _extract_and_write_files(response: str, workspace_path: str) -> dict[str, str]:
    """<FILE> bloklarını çıkarır ve diske yazar."""
    pattern = r'<FILE path="([^"]+)">(.*?)</FILE>'
    matches = re.findall(pattern, response, re.DOTALL)
    written = {}
    for file_path, content in matches:
        full_path = f"{workspace_path}/{file_path}"
        try:
            await _file_tools.write_file(full_path, content.strip())
            written[file_path] = content.strip()
        except Exception:
            written[file_path] = content.strip()
    return written


async def code_gen_node(state: AgentState) -> dict:
    """Kod üretir, tool çağrıları yapar ve dosyaları yazar."""
    model = state.get("model", "claude")
    client = _get_client(model)
    workspace = state.get("workspace_path", "workspace/default")
    iteration = state.get("iteration", 0)

    system = _build_system_prompt()
    user_msg = _build_user_message(state)

    # Geçmiş mesajlar + yeni kullanıcı mesajı
    history = [m for m in state.get("messages", []) if m.get("role") in ("user", "assistant")]
    messages = history + [{"role": "user", "content": user_msg}]

    try:
        # İlk LLM çağrısı
        response = await client.chat(messages, system=system)

        # Tool çağrılarını işle (varsa)
        tool_loop_count = 0
        while "<TOOL_CALL>" in response and tool_loop_count < MAX_TOOL_CALLS:
            clean_resp, tool_results = await _process_tool_calls(response)
            tool_loop_count += 1

            if tool_results:
                # Tool sonuçlarını mesajlara ekle ve tekrar LLM'e sor
                tool_context = "\n\n".join(tool_results)
                messages = messages + [
                    {"role": "assistant", "content": clean_resp or response},
                    {"role": "user", "content": f"## Tool Sonuçları\n{tool_context}\n\nDevam et."},
                ]
                response = await client.chat(messages, system=system)
            else:
                break

        # Dosyaları çıkar ve yaz
        generated_files = await _extract_and_write_files(response, workspace)

        return {
            "raw_response": response,
            "generated_files": generated_files,
            "iteration": iteration + 1,
            "current_node": "code_gen",
            "messages": [{"role": "assistant", "content": response}],
        }

    except Exception as e:
        return {
            "raw_response": f"Kod üretimi başarısız: {e}",
            "generated_files": {},
            "iteration": iteration + 1,
            "current_node": "code_gen",
            "error": str(e),
            "messages": [{"role": "system", "content": f"[Hata] Kod üretimi: {e}"}],
        }


async def code_gen_stream(state: AgentState) -> AsyncIterator[str]:
    """Kod üretimini stream olarak döner (UI için)."""
    model = state.get("model", "claude")
    client = _get_client(model)
    system = _build_system_prompt()
    user_msg = _build_user_message(state)

    messages = [{"role": "user", "content": user_msg}]
    async for chunk in client.stream_chat(messages, system=system):
        yield chunk
