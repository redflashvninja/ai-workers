import httpx
from bs4 import BeautifulSoup
import anthropic
from agents.base import BaseAgent


SYSTEM = """You are a deep-research specialist. You search the web, read pages, and synthesise findings.

Guidelines:
- Always cite your sources with URLs.
- Distinguish between facts and speculation.
- Summarise clearly — bullet points for key findings, a short paragraph for context.
- When researching people or companies for outreach, focus on publicly available info only.
- Today's date is 2026-05-14."""


def _web_search(query: str, num_results: int = 10) -> list[dict]:
    """DuckDuckGo instant answer API — no API key required."""
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        r = client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
        )
        data = r.json()

    results = []
    if data.get("AbstractText"):
        results.append({
            "title": data.get("Heading", query),
            "snippet": data["AbstractText"],
            "url": data.get("AbstractURL", ""),
            "source": "DuckDuckGo Abstract",
        })
    for item in data.get("RelatedTopics", [])[:num_results]:
        if "Text" in item:
            results.append({
                "title": item.get("Text", "")[:80],
                "snippet": item.get("Text", ""),
                "url": item.get("FirstURL", ""),
                "source": "DuckDuckGo",
            })
    return results[:num_results]


def _fetch_page(url: str, max_chars: int = 4000) -> dict:
    try:
        with httpx.Client(
            timeout=15, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; research-agent/1.0)"}
        ) as client:
            r = client.get(url)
            r.raise_for_status()
    except Exception as e:
        return {"url": url, "error": str(e), "content": ""}

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    return {"url": url, "title": soup.title.string if soup.title else "", "content": text[:max_chars]}


class ResearchAgent(BaseAgent):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__(client, SYSTEM)
        self._register_all()

    def _register_all(self):
        self._register_tool(
            "web_search",
            "Search the web using DuckDuckGo. Returns titles, snippets, and URLs.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
            lambda query, num_results=10: _web_search(query, num_results),
        )

        self._register_tool(
            "fetch_page",
            "Fetch and extract the text content of a web page.",
            {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to fetch"},
                    "max_chars": {"type": "integer", "default": 4000},
                },
                "required": ["url"],
            },
            lambda url, max_chars=4000: _fetch_page(url, max_chars),
        )
