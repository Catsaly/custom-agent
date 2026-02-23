"""File management API routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.tools.file_tools import FileTools
from app.tools.test_tools import TestTools

router = APIRouter(prefix="/files", tags=["files"])
file_tools = FileTools(base_path="workspace")
test_tools = TestTools()


class WriteFileRequest(BaseModel):
    path: str
    content: str


class DeleteFileRequest(BaseModel):
    path: str


class RunCodeRequest(BaseModel):
    code: str
    language: str = "python"


@router.get("/list")
async def list_files(path: str = ""):
    files = await file_tools.list_files(path)
    return {"files": files}


@router.get("/tree")
async def get_tree(path: str = ""):
    tree = await file_tools.get_tree(path)
    return {"tree": tree}


@router.get("/read")
async def read_file(path: str):
    try:
        content = await file_tools.read_file(path)
        language = file_tools.get_language(path)
        return {"content": content, "path": path, "language": language}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/write")
async def write_file(req: WriteFileRequest):
    try:
        result = await file_tools.write_file(req.path, req.content)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete")
async def delete_file(path: str):
    try:
        deleted = await file_tools.delete_file(path)
        return {"success": deleted}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    path = await file_tools.save_uploaded_file(file.filename or "upload", content)
    return {"success": True, "path": path, "filename": file.filename, "size": len(content)}


@router.get("/search")
async def search_files(query: str, path: str = ""):
    results = await file_tools.search_in_files(query, path)
    return {"results": results, "count": len(results)}


@router.post("/run")
async def run_code(req: RunCodeRequest):
    result = await test_tools.run_code_snippet(req.code, req.language)
    return result


@router.post("/lint")
async def lint_code(req: RunCodeRequest):
    result = await test_tools.lint_code(req.code, req.language)
    return result


@router.post("/format")
async def format_code(req: RunCodeRequest):
    formatted = await test_tools.format_code(req.code, req.language)
    return {"formatted": formatted}


@router.post("/test")
async def run_tests(workspace_path: str = "workspace", command: Optional[str] = None):
    result = await test_tools.run_tests(workspace_path, command)
    return result
