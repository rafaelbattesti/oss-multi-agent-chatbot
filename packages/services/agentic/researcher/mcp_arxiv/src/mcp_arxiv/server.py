"""MCP server wrapping the public arXiv API. Exposes a single `arxiv_search` tool."""

from __future__ import annotations

import logging
import os

import arxiv
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

ARXIV_PAGE_SIZE = 10
ARXIV_DELAY_SECONDS = 3.0
ARXIV_NUM_RETRIES = 5
RETRY_EXHAUSTED_STATUSES = {429, 500, 502, 503, 504}

_client = arxiv.Client(
    page_size=ARXIV_PAGE_SIZE,
    delay_seconds=ARXIV_DELAY_SECONDS,
    num_retries=ARXIV_NUM_RETRIES,
)

mcp = FastMCP(
    "arxiv",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


@mcp.tool()
def arxiv_search(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv and return matching papers (title, abstract, url)."""
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers: list[dict] = []
    try:
        for result in _client.results(search):
            papers.append(_paper_dict(result))
    except arxiv.HTTPError as exc:
        if exc.status in RETRY_EXHAUSTED_STATUSES:
            logger.warning("arXiv search failed after retries with HTTP %s", exc.status)
            return []
        raise
    except arxiv.UnexpectedEmptyPageError:
        logger.warning("arXiv search returned an unexpected empty page after retries")
        return []
    return papers


def _paper_dict(result) -> dict:
    return {
        "title": result.title.strip(),
        "summary": result.summary.strip(),
        "url": result.entry_id,
    }


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
