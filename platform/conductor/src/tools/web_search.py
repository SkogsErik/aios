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
            import urllib.request
            import urllib.parse
            import json

            encoded = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            results = self._parse_ddg_html(html, num_results)
            if not results:
                return ToolResult(
                    success=True,
                    output=f"No results found for: {query}",
                )
            lines = [f"Web search results for: {query}", ""]
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. {r['title']}")
                lines.append(f"   {r['snippet']}")
                lines.append(f"   {r['url']}")
                lines.append("")
            return ToolResult(success=True, output="\n".join(lines).strip())
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Web search failed: {e}",
            )

    def _parse_ddg_html(self, html: str, max_results: int) -> list[dict]:
        import re
        results = []
        for block in re.split(r'<div class="result__body"[^>]*>', html)[1:]:
            title_m = re.search(r'<a[^>]*class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet_m = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
            url_m = re.search(r'href="(https?://[^"]+)"', block)
            if title_m:
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ""
                url = url_m.group(1) if url_m else ""
                results.append({"title": title, "snippet": snippet, "url": url})
                if len(results) >= max_results:
                    break
        return results
