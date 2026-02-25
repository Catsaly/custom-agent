"""
IDE API Routes — Tool Calling ile AI Kodlama
============================================
/api/ide/* endpointleri
"""
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.ide_agent import IDEAgent, dispatch_tool
from app.ai.model_registry import resolve_model_id
from app.db.supabase_client import SupabaseClient

_db = SupabaseClient()

router = APIRouter(prefix="/ide", tags=["IDE"])
_agent = IDEAgent()
WORKSPACE_ROOT = Path("workspace")


# ── Request Models ────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    messages: list[dict]
    model_id: str = "claude-opus-4-6"
    api_key: Optional[str] = None
    workspace: str = "default"


class FileWriteRequest(BaseModel):
    path: str
    content: str
    workspace: str = "default"


class FileRenameRequest(BaseModel):
    old_path: str
    new_path: str
    workspace: str = "default"


class CommandRequest(BaseModel):
    command: str
    workspace: str = "default"
    timeout: int = 60


class WorkspaceSyncRequest(BaseModel):
    workspace: str = "default"


# ── Agent SSE Stream ──────────────────────────────────────────────────────────

@router.post("/agent/stream")
async def agent_stream(req: AgentRequest):
    """
    IDE ajanını çalıştırır ve olayları SSE olarak stream eder.
    Events: token | tool_start | tool_result | done | error
    """
    model_id = resolve_model_id(req.model_id)

    async def event_generator():
        try:
            async for event in _agent.run(
                messages=req.messages,
                model_id=model_id,
                api_key=req.api_key,
                workspace=req.workspace,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'end'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── File Operations ───────────────────────────────────────────────────────────

@router.get("/files")
async def list_files(workspace: str = "default"):
    """Workspace dosya ağacını döner."""
    base = WORKSPACE_ROOT / workspace
    base.mkdir(parents=True, exist_ok=True)

    def build_tree(directory: Path, prefix: str = "") -> list[dict]:
        items = []
        try:
            children = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return items
        for child in children:
            if child.name.startswith("."):
                continue
            rel = str(child.relative_to(base))
            if child.is_dir():
                items.append({
                    "type": "dir",
                    "name": child.name,
                    "path": rel,
                    "children": build_tree(child),
                })
            else:
                items.append({
                    "type": "file",
                    "name": child.name,
                    "path": rel,
                    "size": child.stat().st_size,
                })
        return items

    return {"workspace": workspace, "tree": build_tree(base)}


@router.get("/files/read")
async def read_file(path: str, workspace: str = "default"):
    """Dosya içeriğini döner."""
    target = WORKSPACE_ROOT / workspace / path
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Dosya bulunamadı: {path}")
    content = target.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content}


@router.post("/files/write")
async def write_file(req: FileWriteRequest):
    """Dosya oluşturur veya günceller. Supabase varsa arka planda sync eder."""
    target = WORKSPACE_ROOT / req.workspace / req.path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(req.content, encoding="utf-8")
    if _db.available:
        import asyncio as _asyncio
        _asyncio.create_task(
            _db.save_workspace_file(req.workspace, req.path, req.content)
        )
    return {"ok": True, "path": req.path}


@router.delete("/files/delete")
async def delete_file(path: str, workspace: str = "default"):
    """Dosya siler. Supabase'den de kaldırır."""
    target = WORKSPACE_ROOT / workspace / path
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Dosya bulunamadı: {path}")
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
    else:
        target.unlink()
    if _db.available:
        import asyncio as _asyncio
        _asyncio.create_task(_db.delete_workspace_file(workspace, path))
    return {"ok": True, "path": path}


@router.post("/files/rename")
async def rename_file(req: FileRenameRequest):
    """Dosyayı yeniden adlandırır veya taşır."""
    src = WORKSPACE_ROOT / req.workspace / req.old_path
    dst = WORKSPACE_ROOT / req.workspace / req.new_path
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Kaynak bulunamadı: {req.old_path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return {"ok": True, "old": req.old_path, "new": req.new_path}


# ── Workspace Persistence (Supabase) ─────────────────────────────────────────

@router.post("/workspace/push")
async def push_workspace(req: WorkspaceSyncRequest):
    """Disk'teki workspace dosyalarını Supabase'e yükler (push)."""
    if not _db.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış")
    base = WORKSPACE_ROOT / req.workspace
    if not base.exists():
        raise HTTPException(status_code=404, detail=f"Workspace bulunamadı: {req.workspace}")

    saved, skipped = 0, 0
    for file_path in base.rglob("*"):
        if not file_path.is_file():
            continue
        if any(p.startswith(".") for p in file_path.parts):
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            rel = str(file_path.relative_to(base))
            await _db.save_workspace_file(req.workspace, rel, content)
            saved += 1
        except Exception:
            skipped += 1

    return {"ok": True, "saved": saved, "skipped": skipped, "workspace": req.workspace}


@router.post("/workspace/pull")
async def pull_workspace(req: WorkspaceSyncRequest):
    """Supabase'deki workspace dosyalarını diske indirir (pull)."""
    if not _db.available:
        raise HTTPException(status_code=503, detail="Supabase yapılandırılmamış")

    files = await _db.load_workspace_files(req.workspace)
    base = WORKSPACE_ROOT / req.workspace
    restored = 0
    for f in files:
        target = base / f["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f["content"], encoding="utf-8")
        restored += 1

    return {"ok": True, "restored": restored, "workspace": req.workspace}


@router.get("/workspace/status")
async def workspace_status(workspace: str = "default"):
    """Supabase'de bu workspace için kaç dosya kayıtlı."""
    if not _db.available:
        return {"supabase": False, "files": 0}
    files = await _db.load_workspace_files(workspace)
    return {"supabase": True, "files": len(files), "workspace": workspace}


# ── Terminal / Command ────────────────────────────────────────────────────────

@router.post("/terminal/run")
async def run_command(req: CommandRequest):
    """Shell komutu çalıştırır ve çıktıyı döner."""
    result = await dispatch_tool(
        "run_command",
        {"command": req.command, "timeout": req.timeout},
        req.workspace,
    )
    return {"output": result}


@router.post("/terminal/stream")
async def run_command_stream(req: CommandRequest):
    """Shell komutunu stream olarak çalıştırır."""
    import asyncio
    import subprocess as sp
    from app.ai.ide_agent import WORKSPACE_ROOT as WS

    async def output_generator():
        cwd = str(WS / req.workspace)
        os.makedirs(cwd, exist_ok=True)
        try:
            proc = await asyncio.create_subprocess_shell(
                req.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )
            async for line in proc.stdout:
                text = line.decode("utf-8", errors="replace")
                yield f"data: {json.dumps({'type': 'output', 'content': text})}\n\n"
            await proc.wait()
            yield f"data: {json.dumps({'type': 'done', 'code': proc.returncode})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        output_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
