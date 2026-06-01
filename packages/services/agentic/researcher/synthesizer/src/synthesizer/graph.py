"""Synthesizer LangGraph: findings (+ optional critique) -> thesis draft."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from thesis_common.llm import complete_structured
from thesis_common.schemas import Critique, ResearchFindings, ThesisDraft

SYSTEM = (
    "You are a research synthesizer. Given evidence about a topic, produce a single, "
    "specific, falsifiable thesis statement and a concise reasoned argument that grounds "
    "it in the evidence. Prefer novelty and clarity over breadth."
)


class _DraftOut(BaseModel):
    statement: str
    argument: str


class SynthState(TypedDict, total=False):
    findings: dict
    critique: dict | None
    revision: int
    draft: dict


async def _synthesize(state: SynthState) -> dict:
    findings = ResearchFindings(**state["findings"])
    revision = state.get("revision", 0)

    sources_block = "\n".join(
        f"- {s.title}: {s.summary[:280]}" for s in findings.sources
    ) or "(no sources retrieved)"

    feedback = ""
    if state.get("critique"):
        critique = Critique(**state["critique"])
        notes = critique.issues + critique.suggestions
        if notes:
            feedback = "\n\nRevise the thesis to address this feedback:\n" + "\n".join(
                f"- {n}" for n in notes
            )

    human = (
        f"Topic: {findings.topic}\n\n"
        f"Evidence synthesis:\n{findings.synthesis}\n\n"
        f"Sources:\n{sources_block}{feedback}\n\n"
        "Return a thesis statement and the reasoned argument supporting it."
    )

    out = await complete_structured(_DraftOut, SYSTEM, human)
    draft = ThesisDraft(statement=out.statement, argument=out.argument, revision=revision)
    return {"draft": draft.model_dump()}


def build_graph():
    graph = StateGraph(SynthState)
    graph.add_node("synthesize", _synthesize)
    graph.add_edge(START, "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()
