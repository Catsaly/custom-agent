"""Chat API routes — model_id + api_key destekli."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json

from app.ai.client_factory import get_client_for_model
from app.ai.model_registry import resolve_model_id
from app.ai.agent import CodingAgent

router = APIRouter(prefix="/chat", tags=["chat"])
_agent = CodingAgent()


class ChatRequest(BaseModel):
    prompt: str
    model: str = "claude"          # kısa isim veya tam model_id
    model_id: Optional[str] = None  # tam model_id (öncelikli)
    api_key: Optional[str] = None  # kullanıcının API anahtarı
    session_id: Optional[str] = None
    messages: list[dict] = []
    workspace_path: Optional[str] = None


class GenerateProjectRequest(BaseModel):
    description: str
    model: str = "claude"
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    workspace_path: str = "workspace/default"


def _resolve(req) -> tuple[str, Optional[str]]:
    """(model_id, api_key) döner."""
    mid = req.model_id or req.model
    return resolve_model_id(mid), req.api_key


@router.post("/stream")
async def stream_chat(req: ChatRequest):
    model_id, api_key = _resolve(req)
    client = get_client_for_model(model_id, api_key=api_key)

    async def generate():
        try:
            messages = req.messages + [{"role": "user", "content": req.prompt}]
            async for chunk in client.stream_chat(messages):
                data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            err = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/message")
async def chat_message(req: ChatRequest):
    model_id, api_key = _resolve(req)
    client = get_client_for_model(model_id, api_key=api_key)
    try:
        messages = req.messages + [{"role": "user", "content": req.prompt}]
        response = await client.chat(messages)
        return {"response": response, "model": model_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-project")
async def generate_project(req: GenerateProjectRequest):
    model_id, api_key = _resolve(req)

    async def generate():
        try:
            async for chunk in _agent.generate_project(
                description=req.description,
                model=model_id,
                workspace_path=req.workspace_path,
                api_key=api_key,
            ):
                data = json.dumps({"type": "text", "content": chunk})
                yield f"data: {data}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            err = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {err}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/explain")
async def explain_code(payload: dict):
    code = payload.get("code", "")
    model_id = resolve_model_id(payload.get("model_id") or payload.get("model", "claude"))
    api_key = payload.get("api_key")
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    client = get_client_for_model(model_id, api_key=api_key)
    messages = [{"role": "user", "content": f"Explain this code:\n\n```\n{code}\n```"}]
    result = await client.chat(messages)
    return {"explanation": result}


@router.post("/fix")
async def fix_code(payload: dict):
    code = payload.get("code", "")
    error = payload.get("error", "")
    model_id = resolve_model_id(payload.get("model_id") or payload.get("model", "claude"))
    api_key = payload.get("api_key")
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    client = get_client_for_model(model_id, api_key=api_key)
    messages = [{"role": "user", "content": f"Fix this code:\n\n```\n{code}\n```\n\nError: {error}"}]
    result = await client.chat(messages)
    return {"fixed_code": result}
