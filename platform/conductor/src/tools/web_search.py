from __future__ import annotations

from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information. Returns a list of results with titles and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (1-20, default 8).",
                "default": 8,
            },
        },
        "required": ["query"],
    }

    def run(self, **params: str | int | float | bool) -> ToolResult:
        query = params.get("query", "")
        num_results = int(params.get("num_results", 8))
        if not isinstance(query, str) or not query.strip():
            return ToolResult(success=False, output="", error="query must be a non-empty string")
        num_results = max(1, min(num_results, 20))

        try:
            from duckduckgo_search import DDGS
            ddgs = DDGS()
            raw_results = list(ddgs.text(query, max_results=num_results))

            if not raw_results:
                return ToolResult(
                    success=True,
                    output=f"No results found for: {query}",
                )

            lines = [f"Web search results for: {query}", ""]
            for i, r in enumerate(raw_results, 1):
                title = r.get("title", "Untitled")
                snippet = r.get("body", "")
                url = r.get("href", "")
                lines.append(f"{i}. {title}")
                if snippet:
                    lines.append(f"   {snippet[:300]}")
                if url:
                    lines.append(f"   {url}")
                lines.append("")
            return ToolResult(success=True, output="\n".join(lines).strip())

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Web search failed: {e}",
            )
