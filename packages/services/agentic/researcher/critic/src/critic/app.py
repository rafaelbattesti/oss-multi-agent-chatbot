"""A2A entrypoint for the Critic agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve
from thesis_common.schemas import CritiqueRequest, CritiqueResponse

from .graph import build_graph

_graph = build_graph()
SEMANTIC_TAGS = ("critique", "viability-review")


async def handle(payload: CritiqueRequest) -> CritiqueResponse:
    state = {
        "draft": payload.draft.model_dump(),
        "findings": payload.findings.model_dump(),
    }
    result = await _graph.ainvoke(state)
    return CritiqueResponse(critique=result["critique"])


def main() -> None:
    card = build_card(
        name="Critic",
        description="Judges whether a thesis draft is novel, feasible and well grounded.",
        skill_id="critique_thesis",
        public_url=config.PUBLIC_URL,
        input_model=CritiqueRequest,
        output_model=CritiqueResponse,
        semantic_tags=SEMANTIC_TAGS,
    )
    serve(card, handle, request_model=CritiqueRequest, response_model=CritiqueResponse)
