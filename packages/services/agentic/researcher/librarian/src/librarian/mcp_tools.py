"""Thin MCP client: call the arXiv MCP server's `arxiv_search` tool."""

from __future__ import annotations

import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from thesis_common import config


def _loads(value) -> object:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def _coerce(raw) -> list[dict]:
    """Normalize the MCP tool result into a list of paper dicts.

    langchain-mcp-adapters returns a list of content blocks like
    ``{"type": "text", "text": "<json>"}``; the paper payload lives in ``text``.
    Older versions return a JSON string or the list directly, so handle all three.
    """
    items = _loads(raw) if isinstance(raw, str) else raw
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        return []

    papers: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "text" in item and "title" not in item:  # MCP text content block
            inner = _loads(item["text"])
            if isinstance(inner, list):
                papers.extend(p for p in inner if isinstance(p, dict))
            elif isinstance(inner, dict):
                papers.append(inner)
        else:
            papers.append(item)
    return papers


async def arxiv_search(query: str, max_results: int = 5) -> list[dict]:
    client = MultiServerMCPClient(
        {"arxiv": {"url": config.MCP_ARXIV_URL, "transport": "streamable_http"}}
    )
    tools = await client.get_tools()
    tool = next((t for t in tools if t.name == "arxiv_search"), None)
    if tool is None:
        return []
    raw = await tool.ainvoke({"query": query, "max_results": max_results})
    return _coerce(raw)
