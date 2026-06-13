import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class BastionState(TypedDict):
  received_payload: dict[str, Any]
  response_text: str


def build_payload_response_text(payload: dict[str, Any]) -> str:
  return json.dumps({"received_payload": payload}, indent=2, sort_keys=True)


def respond_with_payload(state: BastionState) -> dict[str, str]:
  return {"response_text": build_payload_response_text(state["received_payload"])}


def create_stub_graph():
  graph = StateGraph(BastionState)
  graph.add_node("respond_with_payload", respond_with_payload)
  graph.add_edge(START, "respond_with_payload")
  graph.add_edge("respond_with_payload", END)
  return graph.compile()


def run_stub_graph(payload: dict[str, Any]) -> BastionState:
  return create_stub_graph().invoke({"received_payload": payload})
