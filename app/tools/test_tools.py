"""Code testing and execution tools."""
import asyncio
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional

# Bun kurulu mu kontrol et (başlangıçta bir kez)
_BUN_PATH: str | None = shutil.which("bun") or (
    "/root/.bun/bin/bun" if Path("/root/.bun/bin/bun").exists() else None
)


class TestTools:
    async def run_tests(
        self,
        workspace_path: str,
        test_command: Optional[str] = None,
        timeout: int = 60,
    ) -> dict:
        cmd = test_command or self._detect_test_command(workspace_path)
        if not cmd:
            return {"success": False, "output": "No test command found", "error": ""}

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace"),
                "command": cmd,
            }
        except asyncio.TimeoutError:
            return {"success": False, "output": "", "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    async def run_code_snippet(
        self, code: str, language: str = "python", timeout: int = 30
    ) -> dict:
        if language == "python":
            return await self._run_python(code, timeout)
        elif language in ("javascript", "typescript", "node", "bun"):
            return await self._run_js(code, language, timeout)
        return {"success": False, "output": "", "error": f"Language {language} not supported for direct execution"}

    async def _run_python(self, code: str, timeout: int) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            tmp_path = f.name
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            return {"success": False, "output": "", "error": f"Timeout after {timeout}s"}
        finally:
            os.unlink(tmp_path)

    async def _run_js(self, code: str, language: str, timeout: int) -> dict:
        """JS/TS çalıştırır. Bun varsa Bun kullanır, yoksa node/npx fallback."""
        suffix = ".ts" if language == "typescript" else ".js"
        with tempfile.NamedTemporaryFile(suffix=suffix, mode="w", delete=False) as f:
            f.write(code)
            tmp_path = f.name
        try:
            if _BUN_PATH:
                cmd = [_BUN_PATH, "run", tmp_path]
                runtime = "bun"
            elif language == "typescript":
                cmd = ["npx", "ts-node", tmp_path]
                runtime = "ts-node"
            else:
                cmd = ["node", tmp_path]
                runtime = "node"

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "output": stdout.decode("utf-8", errors="replace"),
                "error": stderr.decode("utf-8", errors="replace"),
                "runtime": runtime,
            }
        except asyncio.TimeoutError:
            return {"success": False, "output": "", "error": f"Timeout after {timeout}s"}
        finally:
            os.unlink(tmp_path)

    async def lint_code(self, code: str, language: str = "python") -> dict:
        if language == "python":
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
                f.write(code)
                tmp_path = f.name
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python3", "-m", "py_compile", tmp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
                return {
                    "valid": proc.returncode == 0,
                    "errors": stderr.decode("utf-8", errors="replace"),
                }
            finally:
                os.unlink(tmp_path)
        return {"valid": True, "errors": "Linting not supported for this language"}

    def _detect_test_command(self, workspace_path: str) -> Optional[str]:
        base = Path(workspace_path)
        if (base / "pytest.ini").exists() or (base / "pyproject.toml").exists():
            return "python -m pytest -v"
        if (base / "package.json").exists():
            return "npm test"
        if (base / "Makefile").exists():
            return "make test"
        if list(base.glob("test_*.py")) or list(base.glob("*_test.py")):
            return "python -m pytest -v"
        return None

    async def format_code(self, code: str, language: str = "python") -> str:
        if language == "python":
            try:
                import black
                return black.format_str(code, mode=black.Mode())
            except Exception:
                return code
        return code
