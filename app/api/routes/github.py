"""GitHub integration API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.tools.github_tools import GitHubTools

router = APIRouter(prefix="/github", tags=["github"])
github_tools = GitHubTools()


class DeployRequest(BaseModel):
    workspace_path: str
    repo_name: str
    commit_message: str = "Deploy from CodeCraft AI"
    branch: str = "main"


class CreateRepoRequest(BaseModel):
    name: str
    description: str = ""
    private: bool = False


class WriteFileRequest(BaseModel):
    repo_name: str
    file_path: str
    content: str
    commit_message: str
    branch: str = "main"


@router.get("/repos")
async def list_repos(limit: int = 30):
    try:
        repos = await github_tools.list_user_repos(limit)
        return {"repos": repos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{name}")
async def get_repo(owner: str, name: str):
    try:
        info = await github_tools.get_repo_info(f"{owner}/{name}")
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/repo/{owner}/{name}/contents")
async def get_contents(
    owner: str, name: str, path: str = "", branch: str = "main"
):
    try:
        contents = await github_tools.fetch_repo_contents(
            f"{owner}/{name}", path, branch
        )
        return {"contents": contents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{name}/file")
async def read_file(owner: str, name: str, path: str, branch: str = "main"):
    try:
        content = await github_tools.read_file_from_repo(
            f"{owner}/{name}", path, branch
        )
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/repo/{owner}/{name}/commits")
async def get_commits(owner: str, name: str, branch: str = "main", limit: int = 10):
    try:
        commits = await github_tools.get_commits(f"{owner}/{name}", branch, limit)
        return {"commits": commits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{name}/analyze")
async def analyze_repo(owner: str, name: str):
    try:
        analysis = await github_tools.analyze_repo(f"{owner}/{name}")
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repo/create")
async def create_repo(req: CreateRepoRequest):
    try:
        result = await github_tools.create_repo(req.name, req.description, req.private)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy")
async def deploy(req: DeployRequest):
    try:
        result = await github_tools.deploy_workspace(
            req.workspace_path, req.repo_name, req.commit_message, req.branch
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file/push")
async def push_file(req: WriteFileRequest):
    try:
        result = await github_tools.create_or_update_file(
            req.repo_name, req.file_path, req.content, req.commit_message, req.branch
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
