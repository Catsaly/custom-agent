"""Main AI coding agent that orchestrates all AI models and tools."""
import asyncio
import json
from typing import AsyncIterator, Optional, Literal
from app.ai.claude_client import ClaudeClient
from app.ai.gemini_client import GeminiClient
from app.ai.glm_client import GLMClient
from app.tools.file_tools import FileTools
from app.tools.github_tools import GitHubTools
from app.tools.search_tools import SearchTools

ModelType = Literal["claude", "gemini", "glm"]

CODING_SYSTEM_PROMPT = """You are CodeCraft AI, an expert full-stack developer and AI coding assistant.
You can:
- Generate, refactor, debug, and explain code
- Create complete web apps, APIs, scripts, and more
- Search the web for documentation and solutions
- Read, write, and manage project files
- Interact with GitHub repositories
- Analyze images and screenshots

Guidelines:
- Write clean, production-quality code
- Use modern best practices and patterns
- Provide complete, runnable code — not fragments
- Explain what you're building and why
- When creating files, use proper structure and naming
- Format code blocks with language tags: ```python, ```typescript, etc.
"""


class CodingAgent:
    def __init__(self):
        self.claude = ClaudeClient()
        self.gemini = GeminiClient()
        self.glm = GLMClient()
        self.file_tools = FileTools()
        self.github_tools = GitHubTools()
        self.search_tools = SearchTools()

    def _get_client(self, model: ModelType):
        return {"claude": self.claude, "gemini": self.gemini, "glm": self.glm}[model]

    async def stream_response(
        self,
        prompt: str,
        model: ModelType = "claude",
        conversation_history: Optional[list[dict]] = None,
        workspace_path: Optional[str] = None,
        system_extra: Optional[str] = None,
    ) -> AsyncIterator[str]:
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": prompt})

        system = CODING_SYSTEM_PROMPT
        if workspace_path:
            system += f"\n\nCurrent workspace: {workspace_path}"
        if system_extra:
            system += f"\n\n{system_extra}"

        client = self._get_client(model)
        async for chunk in client.stream_chat(messages, system=system):
            yield chunk

    async def chat(
        self,
        prompt: str,
        model: ModelType = "claude",
        conversation_history: Optional[list[dict]] = None,
        workspace_path: Optional[str] = None,
    ) -> str:
        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": prompt})
        client = self._get_client(model)
        return await client.chat(messages, system=CODING_SYSTEM_PROMPT)

    async def generate_project(
        self,
        description: str,
        model: ModelType = "claude",
        workspace_path: str = "workspace",
    ) -> AsyncIterator[str]:
        prompt = f"""Create a complete project based on this description:

{description}

Requirements:
1. Generate all necessary files with complete content
2. Include proper project structure
3. Add a README.md with setup instructions
4. Make it production-ready

For each file, output in this exact format:
<FILE path="path/to/file.ext">
file content here
</FILE>

After all files, provide a summary of what was created."""

        full_response = ""
        async for chunk in self.stream_response(prompt, model=model, workspace_path=workspace_path):
            full_response += chunk
            yield chunk

        # Parse and write files from response
        await self._extract_and_write_files(full_response, workspace_path)

    async def _extract_and_write_files(self, response: str, workspace_path: str):
        import re
        pattern = r'<FILE path="([^"]+)">(.*?)</FILE>'
        matches = re.findall(pattern, response, re.DOTALL)
        for file_path, content in matches:
            full_path = f"{workspace_path}/{file_path}"
            await self.file_tools.write_file(full_path, content.strip())

    async def analyze_and_fix(
        self,
        code: str,
        error: str,
        model: ModelType = "claude",
    ) -> str:
        prompt = f"""Analyze this code and fix the error:

Code:
```
{code}
```

Error:
```
{error}
```

Provide the fixed code with explanation."""
        return await self.chat(prompt, model=model)

    async def explain_code(self, code: str, model: ModelType = "claude") -> str:
        prompt = f"""Explain this code clearly and concisely:

```
{code}
```

Cover: purpose, how it works, key concepts used."""
        return await self.chat(prompt, model=model)
