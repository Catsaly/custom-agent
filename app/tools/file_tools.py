"""File system tools for reading, writing, and managing project files."""
import os
import aiofiles
import asyncio
from pathlib import Path
from typing import Optional


class FileTools:
    def __init__(self, base_path: str = "workspace"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        resolved = (self.base_path / path).resolve()
        # Security: prevent path traversal
        if not str(resolved).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Path traversal detected: {path}")
        return resolved

    async def read_file(self, path: str) -> str:
        file_path = self._resolve(path)
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()

    async def write_file(self, path: str, content: str) -> dict:
        file_path = self._resolve(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)
        return {
            "path": str(file_path.relative_to(self.base_path)),
            "size": len(content),
            "lines": content.count("\n") + 1,
        }

    async def delete_file(self, path: str) -> bool:
        file_path = self._resolve(path)
        if file_path.exists():
            if file_path.is_dir():
                import shutil
                await asyncio.to_thread(shutil.rmtree, file_path)
            else:
                file_path.unlink()
            return True
        return False

    async def list_files(self, path: str = "") -> list[dict]:
        dir_path = self._resolve(path) if path else self.base_path
        if not dir_path.exists():
            return []

        files = []
        for item in sorted(dir_path.iterdir()):
            rel = item.relative_to(self.base_path)
            info = {
                "name": item.name,
                "path": str(rel),
                "type": "directory" if item.is_dir() else "file",
                "size": 0,
            }
            if item.is_file():
                info["size"] = item.stat().st_size
                info["extension"] = item.suffix
            files.append(info)
        return files

    async def get_tree(self, path: str = "", max_depth: int = 4) -> dict:
        dir_path = self._resolve(path) if path else self.base_path
        return await self._build_tree(dir_path, max_depth, 0)

    async def _build_tree(self, path: Path, max_depth: int, depth: int) -> dict:
        node = {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "path": str(path.relative_to(self.base_path)),
        }
        if path.is_dir() and depth < max_depth:
            children = []
            for item in sorted(path.iterdir()):
                if not item.name.startswith("."):
                    children.append(
                        await self._build_tree(item, max_depth, depth + 1)
                    )
            node["children"] = children
        elif path.is_file():
            node["size"] = path.stat().st_size
        return node

    async def save_uploaded_file(self, filename: str, content: bytes) -> str:
        uploads_dir = self.base_path / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        file_path = uploads_dir / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        return str(file_path.relative_to(self.base_path))

    async def search_in_files(self, query: str, path: str = "") -> list[dict]:
        dir_path = self._resolve(path) if path else self.base_path
        results = []
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    async with aiofiles.open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = await f.read()
                    for i, line in enumerate(content.splitlines(), 1):
                        if query.lower() in line.lower():
                            results.append({
                                "file": str(file_path.relative_to(self.base_path)),
                                "line": i,
                                "content": line.strip(),
                            })
                except Exception:
                    pass
        return results[:50]

    def get_language(self, filename: str) -> str:
        ext_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "jsx", ".tsx": "tsx", ".html": "html", ".css": "css",
            ".json": "json", ".md": "markdown", ".yaml": "yaml",
            ".yml": "yaml", ".sh": "bash", ".sql": "sql",
            ".rs": "rust", ".go": "go", ".java": "java", ".cpp": "cpp",
        }
        return ext_map.get(Path(filename).suffix.lower(), "text")
