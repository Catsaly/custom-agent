"""Image upload and analysis API routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Literal
from app.tools.image_tools import ImageTools
from app.ai.agent import CodingAgent

router = APIRouter(prefix="/images", tags=["images"])
image_tools = ImageTools()
agent = CodingAgent()


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    prompt: str = Form(default="Describe this image"),
    model: Literal["claude", "gemini", "glm"] = Form(default="claude"),
    analyze: bool = Form(default=True),
):
    content = await file.read()
    media_type = file.content_type or "image/png"

    try:
        processed = await image_tools.process_upload(
            content, media_type, file.filename or "image"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = {
        "filename": processed["filename"],
        "info": processed["info"],
        "media_type": media_type,
    }

    if analyze:
        try:
            if model == "claude":
                analysis = await agent.claude.analyze_image(
                    processed["base64"], media_type, prompt
                )
            elif model == "gemini":
                analysis = await agent.gemini.analyze_image(content, prompt)
            else:
                analysis = await agent.glm.analyze_image(processed["base64"], prompt)
            result["analysis"] = analysis
        except Exception as e:
            result["analysis_error"] = str(e)

    # Save to disk
    saved_path = image_tools.save_to_disk(content, file.filename or "image")
    result["saved_path"] = saved_path

    return result


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(default="What do you see in this image?"),
    model: Literal["claude", "gemini", "glm"] = Form(default="claude"),
):
    content = await file.read()
    media_type = file.content_type or "image/png"

    try:
        processed = await image_tools.process_upload(
            content, media_type, file.filename or "image"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        if model == "claude":
            analysis = await agent.claude.analyze_image(
                processed["base64"], media_type, prompt
            )
        elif model == "gemini":
            analysis = await agent.gemini.analyze_image(content, prompt)
        else:
            analysis = await agent.glm.analyze_image(processed["base64"], prompt)
        return {"analysis": analysis, "model": model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
