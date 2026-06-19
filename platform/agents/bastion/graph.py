import json
from typing import TypedDict

from a2a.server.agent_execution import RequestContext
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph

from skills.decompose_query import OUTPUT_SCHEMA

llm = ChatOllama(
    model="gemma4",
    base_url="http://host.docker.internal:11434",
    format=OUTPUT_SCHEMA,
    disable_streaming=True
)

SYSTEM_PROMPT = "Decompose the user query into structured components."


class BastionState(TypedDict):
    query: str
    result: dict


def decompose_query(state: BastionState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["query"])]
    response = llm.invoke(messages)
    return {"result": json.loads(response.content)}


graph = (
    StateGraph(BastionState)
    .add_edge(START, "decompose_query")
    .add_node("decompose_query", decompose_query)
    .add_edge("decompose_query", END)
    .compile()
)


def invoke(context: RequestContext) -> dict:
    state = BastionState(query=context.get_user_input())
    result: BastionState = graph.invoke(state, config={"configurable": {"thread_id": context.context_id}})
    return result["result"]
