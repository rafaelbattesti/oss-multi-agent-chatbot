"""Researcher LangGraph: topic -> arXiv query -> fetch (MCP) -> synthesized findings."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from thesis_common.llm import complete_text
from thesis_common.schemas import ResearchFindings, Source

from .mcp_tools import arxiv_search

QUERY_SYSTEM = (
    "You turn a research topic into a concise arXiv search query of at most 8 words. "
    "Return only the query terms, with no punctuation, quotes, or explanation."
)
SUMMARY_SYSTEM = (
    "You are a research analyst. In 4-6 sentences, synthesize the key findings, methods, "
    "and open questions across the given paper abstracts, focused on the topic."
)


class ResearchState(TypedDict, total=False):
    topic: str
    query: str
    sources: list[dict]
    findings: dict


async def _plan(state: ResearchState) -> dict:
    query = await complete_text(QUERY_SYSTEM, f"Topic: {state['topic']}", temperature=0.0)
    return {"query": query.strip().strip('"').strip()[:200]}


async def _fetch(state: ResearchState) -> dict:
    papers = await arxiv_search(state["query"], max_results=5)
    sources = [
        Source(
            title=p.get("title", ""),
            summary=p.get("summary", ""),
            url=p.get("url", ""),
        ).model_dump()
        for p in papers
    ]
    return {"sources": sources}


async def _summarize(state: ResearchState) -> dict:
    sources = state.get("sources", [])
    if sources:
        abstracts = "\n\n".join(f"{s['title']}\n{s['summary'][:600]}" for s in sources)
        human = f"Topic: {state['topic']}\n\nAbstracts:\n{abstracts}"
    else:
        human = (
            "No papers were retrieved. Summarize what is generally known and the key "
            f"open questions about: {state['topic']}"
        )
    synthesis = await complete_text(SUMMARY_SYSTEM, human)
    findings = ResearchFindings(
        topic=state["topic"],
        sources=[Source(**s) for s in sources],
        synthesis=synthesis.strip(),
    )
    return {"findings": findings.model_dump()}


def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("plan", _plan)
    graph.add_node("fetch", _fetch)
    graph.add_node("summarize", _summarize)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "fetch")
    graph.add_edge("fetch", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()
