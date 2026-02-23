"""Chat API routes with streaming support."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal
import json
import uuid

from app.ai.agent import CodingAgent

router = APIRouter(prefix="/chat", tags=["chat"])
agent = CodingAgent()


class ChatRequest(BaseModel):
    prompt: str
    model: Literal["claude", "gemini", "glm"] = "claude"
    session_id: Optional[str] = None
    messages: list[dict] = []
    workspace_path: Optional[str] = None


class GenerateProjectRequest(BaseModel):
    description: str
    model: Literal["claude", "gemini", "glm"] = "claude"
    workspace_path: str = "workspace/default"


@router.post("/stream")
async def stream_chat(req: ChatRequest):
    async def generate():
        try:
            async for chunk in agent.stream_response(
                prompt=req.prompt,
                model=req.model,
                conversation_history=req.messages,
                workspace_path=req.workspace_path,
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
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/message")
async def chat_message(req: ChatRequest):
    try:
        response = await agent.chat(
            prompt=req.prompt,
            model=req.model,
            conversation_history=req.messages,
            workspace_path=req.workspace_path,
        )
        return {"response": response, "model": req.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-project")
async def generate_project(req: GenerateProjectRequest):
    async def generate():
        try:
            async for chunk in agent.generate_project(
                description=req.description,
                model=req.model,
                workspace_path=req.workspace_path,
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
    model = payload.get("model", "claude")
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    result = await agent.explain_code(code, model=model)
    return {"explanation": result}


@router.post("/fix")
async def fix_code(payload: dict):
    code = payload.get("code", "")
    error = payload.get("error", "")
    model = payload.get("model", "claude")
    if not code:
        raise HTTPException(status_code=400, detail="code is required")
    result = await agent.analyze_and_fix(code, error, model=model)
    return {"fixed_code": result}
