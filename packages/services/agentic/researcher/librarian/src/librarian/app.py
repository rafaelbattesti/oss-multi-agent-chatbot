"""A2A entrypoint for the Researcher agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve
from thesis_common.schemas import ResearchRequest, ResearchResponse

from .graph import build_graph

_graph = build_graph()
SEMANTIC_TAGS = ("research", "evidence", "arxiv", "mcp")


async def handle(payload: ResearchRequest) -> ResearchResponse:
    result = await _graph.ainvoke({"topic": payload.topic})
    return ResearchResponse(findings=result["findings"])


def main() -> None:
    card = build_card(
        name="Researcher",
        description="Gathers arXiv evidence via MCP and synthesizes research findings.",
        skill_id="gather_evidence",
        public_url=config.PUBLIC_URL,
        input_model=ResearchRequest,
        output_model=ResearchResponse,
        semantic_tags=SEMANTIC_TAGS,
    )
    serve(card, handle, request_model=ResearchRequest, response_model=ResearchResponse)
