"""
src/tools/web_search.py
Stub web search tool — swap the body of `search()` with a real HTTP call
(e.g. SerpAPI, Brave Search, Tavily) once you have an API key.
"""

WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": "Search the web for current information. Returns a short summary.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            }
        },
        "required": ["query"],
    },
}


def search(query: str) -> str:
    """
    Execute a web search.

    Replace this stub with a real implementation:
        import httpx
        resp = httpx.get("https://api.search-provider.com/search", params={"q": query, "api_key": KEY})
        return resp.json()["results"][0]["snippet"]
    """
    # Stub: return a placeholder so the agent loop still works for demos
    return f"[stub] No real search performed. Query was: '{query}'"


def run_web_search(tool_input: dict) -> str:
    """Execute the web_search tool given raw tool_input from the API."""
    return search(tool_input["query"])
