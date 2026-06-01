"""A2A entrypoint for the Librarian agent."""

from __future__ import annotations

import config
from a2a_core import build_card, serve
from thesis_contracts import ResearchRequest, ResearchResponse

from .graph import build_graph

_graph = build_graph()
SEMANTIC_TAGS = ("research", "evidence", "arxiv", "mcp")


async def handle(payload: ResearchRequest) -> ResearchResponse:
    result = await _graph.ainvoke({"topic": payload.topic})
    return ResearchResponse(findings=result["findings"])


def main() -> None:
    card = build_card(
        name="Librarian",
        description="Gathers arXiv evidence via MCP and synthesizes research findings.",
        skill_id="gather_evidence",
        public_url=config.PUBLIC_URL,
        input_model=ResearchRequest,
        output_model=ResearchResponse,
        semantic_tags=SEMANTIC_TAGS,
    )
    serve(card, handle, request_model=ResearchRequest)
