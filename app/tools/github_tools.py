"""GitHub integration tools for fetching repos, creating branches, and deploying."""
import asyncio
import base64
from typing import Optional
from pathlib import Path
from app.config import settings


class GitHubTools:
    def __init__(self):
        self._github = None

    def _get_github(self):
        if self._github is None:
            from github import Github
            self._github = Github(settings.github_token)
        return self._github

    async def get_repo_info(self, repo_name: str) -> dict:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
                "default_branch": repo.default_branch,
                "topics": repo.get_topics(),
                "created_at": str(repo.created_at),
                "updated_at": str(repo.updated_at),
            }
        return await asyncio.to_thread(_fetch)

    async def fetch_repo_contents(
        self, repo_name: str, path: str = "", branch: str = "main"
    ) -> list[dict]:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            contents = repo.get_contents(path, ref=branch)
            result = []
            for item in (contents if isinstance(contents, list) else [contents]):
                result.append({
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "sha": item.sha,
                    "download_url": item.download_url,
                })
            return result
        return await asyncio.to_thread(_fetch)

    async def read_file_from_repo(
        self, repo_name: str, file_path: str, branch: str = "main"
    ) -> str:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=branch)
            return base64.b64decode(content.content).decode("utf-8")
        return await asyncio.to_thread(_fetch)

    async def create_or_update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
    ) -> dict:
        def _push():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            encoded = base64.b64encode(content.encode()).decode()
            try:
                existing = repo.get_contents(file_path, ref=branch)
                result = repo.update_file(
                    file_path, commit_message, content, existing.sha, branch=branch
                )
                return {"action": "updated", "sha": result["commit"].sha}
            except Exception:
                result = repo.create_file(
                    file_path, commit_message, content, branch=branch
                )
                return {"action": "created", "sha": result["commit"].sha}
        return await asyncio.to_thread(_push)

    async def create_repo(
        self, name: str, description: str = "", private: bool = False
    ) -> dict:
        def _create():
            g = self._get_github()
            user = g.get_user()
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True,
            )
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "clone_url": repo.clone_url,
            }
        return await asyncio.to_thread(_create)

    async def list_user_repos(self, limit: int = 30) -> list[dict]:
        def _list():
            g = self._get_github()
            user = g.get_user()
            return [
                {
                    "name": r.name,
                    "full_name": r.full_name,
                    "description": r.description,
                    "language": r.language,
                    "stars": r.stargazers_count,
                    "url": r.html_url,
                    "updated_at": str(r.updated_at),
                }
                for r in user.get_repos()[:limit]
            ]
        return await asyncio.to_thread(_list)

    async def deploy_workspace(
        self,
        workspace_path: str,
        repo_name: str,
        commit_message: str = "Deploy from CodeCraft AI",
        branch: str = "main",
    ) -> dict:
        results = []
        base = Path(workspace_path)
        for file_path in base.rglob("*"):
            if file_path.is_file() and not any(
                p.startswith(".") for p in file_path.parts
            ):
                rel = str(file_path.relative_to(base))
                try:
                    content = file_path.read_text(encoding="utf-8")
                    result = await self.create_or_update_file(
                        repo_name, rel, content,
                        f"{commit_message}: {rel}", branch
                    )
                    results.append({"file": rel, "status": "ok", **result})
                except Exception as e:
                    results.append({"file": rel, "status": "error", "error": str(e)})
        return {
            "deployed": len([r for r in results if r["status"] == "ok"]),
            "errors": len([r for r in results if r["status"] == "error"]),
            "files": results,
        }

    async def get_commits(
        self, repo_name: str, branch: str = "main", limit: int = 10
    ) -> list[dict]:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            return [
                {
                    "sha": c.sha[:7],
                    "message": c.commit.message.split("\n")[0],
                    "author": c.commit.author.name,
                    "date": str(c.commit.author.date),
                    "url": c.html_url,
                }
                for c in repo.get_commits(sha=branch)[:limit]
            ]
        return await asyncio.to_thread(_fetch)

    async def analyze_repo(self, repo_name: str) -> str:
        info = await self.get_repo_info(repo_name)
        contents = await self.fetch_repo_contents(repo_name)
        readme = ""
        try:
            readme = await self.read_file_from_repo(repo_name, "README.md")
        except Exception:
            pass

        summary = f"""Repository: {info['full_name']}
Description: {info.get('description', 'N/A')}
Language: {info.get('language', 'N/A')}
Stars: {info['stars']} | Forks: {info['forks']}
Files: {len(contents)}

Root files: {', '.join(c['name'] for c in contents[:20])}

README preview:
{readme[:500] if readme else 'No README found'}"""
        return summary
