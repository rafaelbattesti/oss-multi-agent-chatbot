"""A2A entrypoint for the Synthesizer agent."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve
from thesis_common.schemas import SynthesisRequest, SynthesisResponse

from .graph import build_graph

_graph = build_graph()
SEMANTIC_TAGS = ("synthesis", "thesis-draft")


async def handle(payload: SynthesisRequest) -> SynthesisResponse:
    state = {
        "findings": payload.findings.model_dump(),
        "critique": payload.critique.model_dump() if payload.critique else None,
        "revision": payload.revision,
    }
    result = await _graph.ainvoke(state)
    return SynthesisResponse(draft=result["draft"])


def main() -> None:
    card = build_card(
        name="Synthesizer",
        description="Composes a thesis statement and reasoned argument from research findings.",
        skill_id="synthesize_thesis",
        public_url=config.PUBLIC_URL,
        input_model=SynthesisRequest,
        output_model=SynthesisResponse,
        semantic_tags=SEMANTIC_TAGS,
    )
    serve(card, handle, request_model=SynthesisRequest, response_model=SynthesisResponse)
