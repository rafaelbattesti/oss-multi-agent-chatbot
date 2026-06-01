"""A2A entrypoint for the Coordinator agent (the system's public entry point)."""

from __future__ import annotations

from thesis_common import config
from thesis_common.a2a_server import build_card, serve
from thesis_common.schemas import ThesisRequest, ThesisResult

from .graph import build_graph

_graph = build_graph()
SEMANTIC_TAGS = ("orchestration", "thesis")


async def handle(payload: ThesisRequest) -> ThesisResult:
    result = await _graph.ainvoke({"topic": payload.topic, "revisions": 0})
    return ThesisResult(**result["result"])


def main() -> None:
    card = build_card(
        name="ThesisCoordinator",
        description=(
            "Produces a reasoned, viable research thesis from a topic by "
            "orchestrating specialist agents."
        ),
        skill_id="produce_thesis",
        public_url=config.PUBLIC_URL,
        input_model=ThesisRequest,
        output_model=ThesisResult,
        semantic_tags=SEMANTIC_TAGS,
    )
    serve(card, handle, request_model=ThesisRequest, response_model=ThesisResult)
