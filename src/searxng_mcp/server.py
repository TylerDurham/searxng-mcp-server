import os
from typing import Any, Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .fetch import FetchError, fetch_page
from .searxng import SearXNGClient, SearXNGError

load_dotenv()

mcp = FastMCP("searxng-mcp")


@mcp.tool
async def search(
    query: str,
    max_results: int = 10,
    categories: str | None = None,
    language: str | None = None,
    time_range: Literal["day", "month", "year"] | None = None,
    page: int = 1,
) -> dict[str, Any]:
    """Search the web using SearXNG.

    Args:
        query: The search query.
        max_results: Maximum number of results to return.
        categories: Comma-separated SearXNG categories, e.g. "general", "news", "it".
        language: Language code, e.g. "en" or "en-US". Defaults to SEARXNG_LANGUAGE.
        time_range: Only return results from the last day, month, or year.
        page: Results page number, starting at 1.
    """
    try:
        async with SearXNGClient() as client:
            data = await client.search(
                query,
                categories=categories,
                language=language,
                time_range=time_range,
                page=page,
            )
    except SearXNGError as e:
        raise ToolError(str(e)) from e

    results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
            "engine": r.get("engine"),
        }
        for r in data.get("results", [])[:max_results]
    ]
    return {
        "query": query,
        "results": results,
        "answers": data.get("answers", []),
        "suggestions": data.get("suggestions", []),
    }


@mcp.tool
async def fetch(url: str, max_length: int = 20000) -> dict[str, Any]:
    """Fetch a web page and return its main content as Markdown.

    Args:
        url: The http or https URL to fetch.
        max_length: Maximum number of characters of content to return.
    """
    try:
        return await fetch_page(url, max_length)
    except FetchError as e:
        raise ToolError(str(e)) from e


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "http":
        mcp.run(
            transport="http",
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
    else:
        mcp.run()


if __name__ == "__main__":
    main()
