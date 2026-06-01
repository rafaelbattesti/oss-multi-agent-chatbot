"""Critic LangGraph: thesis draft + findings -> viability verdict."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from thesis_common.llm import complete_structured
from thesis_common.schemas import Critique, ResearchFindings, ThesisDraft

SYSTEM = (
    "You are a rigorous research critic. Judge whether a proposed thesis is VIABLE: "
    "novel, feasible to investigate, and grounded in the cited evidence. Be strict. "
    "Mark viable=true only if it clears all three bars. List concrete issues and "
    "actionable suggestions."
)


class _CritiqueOut(BaseModel):
    viable: bool
    issues: list[str]
    suggestions: list[str]


class CriticState(TypedDict, total=False):
    draft: dict
    findings: dict
    critique: dict


async def _critique(state: CriticState) -> dict:
    draft = ThesisDraft(**state["draft"])
    findings = ResearchFindings(**state["findings"])

    human = (
        f"Topic: {findings.topic}\n\n"
        f"Proposed thesis statement:\n{draft.statement}\n\n"
        f"Argument:\n{draft.argument}\n\n"
        f"Evidence available:\n{findings.synthesis}\n\n"
        "Assess novelty, feasibility, and grounding, then return the verdict."
    )

    out = await complete_structured(_CritiqueOut, SYSTEM, human)
    critique = Critique(viable=out.viable, issues=out.issues, suggestions=out.suggestions)
    return {"critique": critique.model_dump()}


def build_graph():
    graph = StateGraph(CriticState)
    graph.add_node("critique", _critique)
    graph.add_edge(START, "critique")
    graph.add_edge("critique", END)
    return graph.compile()
