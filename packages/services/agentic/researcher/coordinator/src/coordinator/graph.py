"""Coordinator LangGraph: orchestrates the specialist agents over A2A.

Flow: research (once) -> [ synthesize -> critique ]*  with a bounded refine loop.
The loop repeats while the Critic rejects viability and revisions < MAX_REVISIONS.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from thesis_common import config
from thesis_common.a2a_client import call_agent
from thesis_common.schemas import (
    Critique,
    CritiqueRequest,
    CritiqueResponse,
    ResearchFindings,
    ResearchRequest,
    ResearchResponse,
    SynthesisRequest,
    SynthesisResponse,
    ThesisDraft,
    ThesisResult,
)

logger = logging.getLogger(__name__)


class CoordState(TypedDict, total=False):
    topic: str
    findings: dict
    draft: dict
    critique: dict
    revisions: int
    result: dict


async def _research(state: CoordState) -> dict:
    logger.info("Coordinator started the research step.")
    response = await call_agent(
        config.RESEARCHER_URL,
        ResearchRequest(topic=state["topic"]),
        ResearchResponse,
    )
    logger.info(
        "Coordinator completed the research step with %s source(s).",
        len(response.findings.sources),
    )
    return {"findings": response.findings.model_dump()}


async def _synthesize(state: CoordState) -> dict:
    critique = Critique(**state["critique"]) if state.get("critique") else None
    revision = state.get("revisions", 0)
    logger.info(
        "Coordinator started synthesis revision %s with critique feedback: %s.",
        revision,
        critique is not None,
    )
    payload = SynthesisRequest(
        findings=ResearchFindings(**state["findings"]),
        critique=critique,
        revision=revision,
    )
    response = await call_agent(config.SYNTHESIZER_URL, payload, SynthesisResponse)
    logger.info("Coordinator completed synthesis revision %s.", revision)
    return {"draft": response.draft.model_dump()}


async def _critique(state: CoordState) -> dict:
    logger.info(
        "Coordinator started critique after revision %s.",
        state.get("revisions", 0),
    )
    payload = CritiqueRequest(
        draft=ThesisDraft(**state["draft"]),
        findings=ResearchFindings(**state["findings"]),
    )
    response = await call_agent(config.CRITIC_URL, payload, CritiqueResponse)
    logger.info(
        "Coordinator completed critique. Viable: %s. Next revision count: %s.",
        response.critique.viable,
        state.get("revisions", 0) + 1,
    )
    return {
        "critique": response.critique.model_dump(),
        "revisions": state.get("revisions", 0) + 1,
    }


def _route(state: CoordState) -> str:
    critique = Critique(**state["critique"])
    if critique.viable or state["revisions"] >= config.MAX_REVISIONS:
        logger.info(
            "Coordinator routing to finalize. Viable: %s. Revisions: %s of %s.",
            critique.viable,
            state["revisions"],
            config.MAX_REVISIONS,
        )
        return "finalize"
    logger.info(
        "Coordinator routing back to synthesize. Viable: %s. Revisions: %s of %s.",
        critique.viable,
        state["revisions"],
        config.MAX_REVISIONS,
    )
    return "synthesize"


async def _finalize(state: CoordState) -> dict:
    logger.info("Coordinator started finalization after %s revision(s).", state["revisions"])
    findings = ResearchFindings(**state["findings"])
    draft = ThesisDraft(**state["draft"])
    critique = Critique(**state["critique"])
    result = ThesisResult(
        topic=state["topic"],
        statement=draft.statement,
        argument=draft.argument,
        viability=critique,
        sources=findings.sources,
        revisions=state["revisions"],
    )
    logger.info(
        "Coordinator completed finalization. Viable: %s. Sources: %s. Revisions: %s.",
        critique.viable,
        len(findings.sources),
        state["revisions"],
    )
    return {"result": result.model_dump()}


def build_graph():
    graph = StateGraph(CoordState)
    graph.add_node("research", _research)
    graph.add_node("synthesize", _synthesize)
    graph.add_node("critique", _critique)
    graph.add_node("finalize", _finalize)
    graph.add_edge(START, "research")
    graph.add_edge("research", "synthesize")
    graph.add_edge("synthesize", "critique")
    graph.add_conditional_edges(
        "critique", _route, {"synthesize": "synthesize", "finalize": "finalize"}
    )
    graph.add_edge("finalize", END)
    return graph.compile()
