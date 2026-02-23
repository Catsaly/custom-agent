"""
GitHub Context Provider
=======================
GitHub API'den veri çekerek LLM'e zengin bağlam sağlar.

Kullanım:
    provider = GitHubContextProvider()
    context = await provider.get_repo_context("owner/repo")
    # LLM'e system prompt olarak enjekte et
"""

import asyncio
import base64
from typing import Optional
from app.config import settings


TECH_STACK_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
    "mix.exs",
    ".nvmrc",
    "Dockerfile",
    "docker-compose.yml",
    ".python-version",
]


class GitHubContextProvider:
    """GitHub API'den akıllıca veri çekerek LLM'e bağlam sağlar."""

    def __init__(self):
        self._github = None

    def _get_github(self):
        if self._github is None:
            from github import Github
            token = settings.github_token
            self._github = Github(token) if token else Github()
        return self._github

    # ── Repo Context ─────────────────────────────────────────────────────────

    async def get_repo_context(
        self,
        repo_name: str,
        include_issues: bool = True,
        include_prs: bool = True,
        include_commits: bool = True,
        issue_limit: int = 5,
        pr_limit: int = 5,
        commit_limit: int = 5,
    ) -> str:
        """Repo için kapsamlı LLM bağlamı oluşturur."""
        tasks = [
            self._fetch_repo_info(repo_name),
            self._fetch_readme(repo_name),
            self._fetch_tech_stack(repo_name),
            self._fetch_directory_tree(repo_name),
        ]
        if include_issues:
            tasks.append(self._fetch_issues(repo_name, issue_limit))
        if include_prs:
            tasks.append(self._fetch_prs(repo_name, pr_limit))
        if include_commits:
            tasks.append(self._fetch_commits(repo_name, commit_limit))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        info = results[0] if not isinstance(results[0], Exception) else {}
        readme = results[1] if not isinstance(results[1], Exception) else ""
        tech = results[2] if not isinstance(results[2], Exception) else {}
        tree = results[3] if not isinstance(results[3], Exception) else []
        issues = results[4] if len(results) > 4 and not isinstance(results[4], Exception) else []
        prs = results[5] if len(results) > 5 and not isinstance(results[5], Exception) else []
        commits = results[6] if len(results) > 6 and not isinstance(results[6], Exception) else []

        return self._format_repo_context(info, readme, tech, tree, issues, prs, commits)

    async def get_file_context(self, repo_name: str, file_path: str, branch: str = "main") -> str:
        """Belirli bir dosyanın içeriğini getirir."""
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            try:
                content = repo.get_contents(file_path, ref=branch)
                return base64.b64decode(content.content).decode("utf-8")
            except Exception:
                # Try HEAD branch
                try:
                    content = repo.get_contents(file_path)
                    return base64.b64decode(content.content).decode("utf-8")
                except Exception as e:
                    return f"[Dosya okunamadı: {e}]"
        return await asyncio.to_thread(_fetch)

    async def search_repos(self, query: str, limit: int = 5) -> str:
        """GitHub'da repo arar ve özetler."""
        def _search():
            g = self._get_github()
            repos = g.search_repositories(query=query, sort="stars", order="desc")
            results = []
            for repo in repos[:limit]:
                results.append(
                    f"• {repo.full_name} ⭐{repo.stargazers_count}\n"
                    f"  {repo.description or 'Açıklama yok'}\n"
                    f"  Dil: {repo.language} | URL: {repo.html_url}"
                )
            return "\n\n".join(results) if results else "Sonuç bulunamadı."
        try:
            return await asyncio.to_thread(_search)
        except Exception as e:
            return f"[Arama hatası: {e}]"

    async def search_code(self, query: str, repo: Optional[str] = None, limit: int = 5) -> str:
        """GitHub'da kod arar."""
        def _search():
            g = self._get_github()
            q = query if not repo else f"{query} repo:{repo}"
            results_raw = g.search_code(query=q)
            results = []
            for item in results_raw[:limit]:
                try:
                    content_raw = base64.b64decode(item.decoded_content).decode("utf-8")
                    snippet = "\n".join(content_raw.splitlines()[:20])
                except Exception:
                    snippet = "[içerik okunamadı]"
                results.append(
                    f"### {item.repository.full_name} — {item.path}\n"
                    f"URL: {item.html_url}\n"
                    f"```\n{snippet}\n```"
                )
            return "\n\n".join(results) if results else "Sonuç bulunamadı."
        try:
            return await asyncio.to_thread(_search)
        except Exception as e:
            return f"[Kod arama hatası: {e}]"

    # ── Private Fetchers ─────────────────────────────────────────────────────

    async def _fetch_repo_info(self, repo_name: str) -> dict:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            return {
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "topics": repo.get_topics(),
                "license": repo.license.name if repo.license else None,
                "default_branch": repo.default_branch,
                "created_at": str(repo.created_at.date()),
                "updated_at": str(repo.updated_at.date()),
                "url": repo.html_url,
                "size_kb": repo.size,
            }
        return await asyncio.to_thread(_fetch)

    async def _fetch_readme(self, repo_name: str, max_chars: int = 2000) -> str:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            try:
                readme = repo.get_readme()
                content = base64.b64decode(readme.content).decode("utf-8")
                return content[:max_chars] + ("..." if len(content) > max_chars else "")
            except Exception:
                return ""
        return await asyncio.to_thread(_fetch)

    async def _fetch_tech_stack(self, repo_name: str) -> dict:
        """Teknoloji stack dosyalarını okur (package.json, requirements.txt, vb.)"""
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            found = {}
            for filename in TECH_STACK_FILES:
                try:
                    f = repo.get_contents(filename)
                    content = base64.b64decode(f.content).decode("utf-8")
                    found[filename] = content[:1500]
                except Exception:
                    continue
            return found
        return await asyncio.to_thread(_fetch)

    async def _fetch_directory_tree(self, repo_name: str, max_depth: int = 2) -> list:
        """Root dizin ağacını getirir."""
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            try:
                tree = repo.get_git_tree(repo.default_branch, recursive=True)
                paths = []
                for item in tree.tree:
                    depth = item.path.count("/")
                    if depth <= max_depth:
                        paths.append({"path": item.path, "type": item.type, "size": item.size})
                return paths[:100]  # Max 100 item
            except Exception:
                try:
                    contents = repo.get_contents("")
                    return [{"path": c.name, "type": c.type, "size": c.size}
                            for c in contents]
                except Exception:
                    return []
        return await asyncio.to_thread(_fetch)

    async def _fetch_issues(self, repo_name: str, limit: int = 5) -> list:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            issues = []
            for issue in repo.get_issues(state="open", sort="created", direction="desc")[:limit]:
                if issue.pull_request:
                    continue  # skip PRs
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "labels": [l.name for l in issue.labels],
                    "created_at": str(issue.created_at.date()),
                    "url": issue.html_url,
                    "body_preview": (issue.body or "")[:300],
                })
            return issues
        return await asyncio.to_thread(_fetch)

    async def _fetch_prs(self, repo_name: str, limit: int = 5) -> list:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            prs = []
            for pr in repo.get_pulls(state="open", sort="created", direction="desc")[:limit]:
                prs.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "author": pr.user.login,
                    "created_at": str(pr.created_at.date()),
                    "changed_files": pr.changed_files,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "url": pr.html_url,
                    "body_preview": (pr.body or "")[:200],
                })
            return prs
        return await asyncio.to_thread(_fetch)

    async def _fetch_commits(self, repo_name: str, limit: int = 5) -> list:
        def _fetch():
            g = self._get_github()
            repo = g.get_repo(repo_name)
            commits = []
            for c in repo.get_commits()[:limit]:
                commits.append({
                    "sha": c.sha[:7],
                    "message": c.commit.message.split("\n")[0],
                    "author": c.commit.author.name,
                    "date": str(c.commit.author.date.date()),
                })
            return commits
        return await asyncio.to_thread(_fetch)

    # ── Formatter ─────────────────────────────────────────────────────────────

    def _format_repo_context(
        self,
        info: dict,
        readme: str,
        tech: dict,
        tree: list,
        issues: list,
        prs: list,
        commits: list,
    ) -> str:
        sections = []

        # Repo Info
        if info:
            topics = ", ".join(info.get("topics", [])) or "—"
            sections.append(
                f"## GitHub Repo: {info.get('full_name', '?')}\n"
                f"**Açıklama:** {info.get('description') or '—'}\n"
                f"**Dil:** {info.get('language') or '—'} | "
                f"**Stars:** {info.get('stars', 0)} | "
                f"**Forks:** {info.get('forks', 0)} | "
                f"**Açık Issues:** {info.get('open_issues', 0)}\n"
                f"**Konular:** {topics}\n"
                f"**Lisans:** {info.get('license') or '—'} | "
                f"**Branch:** {info.get('default_branch', 'main')}\n"
                f"**Boyut:** {info.get('size_kb', 0)} KB | "
                f"**URL:** {info.get('url', '')}"
            )

        # Tech Stack
        if tech:
            tech_lines = []
            for fname, content in tech.items():
                tech_lines.append(f"### `{fname}`\n```\n{content}\n```")
            sections.append("## Teknoloji Stack Dosyaları\n" + "\n\n".join(tech_lines))

        # Directory Tree
        if tree:
            dirs = [t for t in tree if t["type"] == "tree"]
            files = [t for t in tree if t["type"] == "blob"]
            tree_str = "```\n"
            for d in dirs[:20]:
                tree_str += f"📁 {d['path']}/\n"
            for f in files[:30]:
                size = f.get("size", 0)
                size_str = f" ({size}B)" if size else ""
                tree_str += f"📄 {f['path']}{size_str}\n"
            tree_str += "```"
            sections.append(f"## Dizin Yapısı\n{tree_str}")

        # README
        if readme:
            sections.append(f"## README (Önizleme)\n```markdown\n{readme}\n```")

        # Recent Issues
        if issues:
            issue_lines = []
            for i in issues:
                labels = f" [{', '.join(i['labels'])}]" if i["labels"] else ""
                issue_lines.append(
                    f"- #{i['number']} **{i['title']}**{labels} ({i['created_at']})\n"
                    f"  {i['body_preview'][:150] if i['body_preview'] else ''}"
                )
            sections.append("## Açık Issues (Son {})\n{}".format(
                len(issues), "\n".join(issue_lines)
            ))

        # Recent PRs
        if prs:
            pr_lines = []
            for pr in prs:
                pr_lines.append(
                    f"- #{pr['number']} **{pr['title']}** by @{pr['author']} "
                    f"(+{pr['additions']}/-{pr['deletions']}, {pr['changed_files']} dosya)"
                )
            sections.append("## Açık Pull Requests\n" + "\n".join(pr_lines))

        # Recent Commits
        if commits:
            commit_lines = [
                f"- `{c['sha']}` {c['message']} — {c['author']} ({c['date']})"
                for c in commits
            ]
            sections.append("## Son Commitler\n" + "\n".join(commit_lines))

        return "\n\n---\n\n".join(sections)
