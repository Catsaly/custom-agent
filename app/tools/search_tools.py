"""Web search and document search tools."""
import asyncio
from typing import Optional


class SearchTools:
    async def web_search(self, query: str, max_results: int = 5) -> list[dict]:
        def _search():
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    }
                    for r in results
                ]
            except Exception as e:
                return [{"error": str(e), "title": "Search failed", "url": "", "snippet": ""}]

        return await asyncio.to_thread(_search)

    async def search_docs(self, query: str, technology: str = "") -> list[dict]:
        search_query = f"{technology} {query} documentation" if technology else f"{query} documentation"
        return await self.web_search(search_query, max_results=5)

    async def find_examples(self, query: str, language: str = "") -> list[dict]:
        search_query = f"{language} {query} example code" if language else f"{query} example code"
        return await self.web_search(search_query, max_results=5)

    def format_search_results(self, results: list[dict]) -> str:
        if not results:
            return "No results found."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', 'Unknown')}**")
            if r.get("url"):
                lines.append(f"   URL: {r['url']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet'][:200]}")
            lines.append("")
        return "\n".join(lines)
