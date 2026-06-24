import json
from typing import TypedDict

from a2a.server.agent_execution import RequestContext
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph

from config import load_config
from skills.decompose_query import OUTPUT_SCHEMA

config = load_config()

llm = ChatOllama(
    model="gemma4",
    base_url=config.ollama_base_url,
    format=OUTPUT_SCHEMA,
    disable_streaming=True
)

SYSTEM_PROMPT = "Decompose the user query into structured components."


class OrchestratorState(TypedDict):
    query: str
    result: dict


def decompose_query(state: OrchestratorState) -> dict:
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["query"])]
    response = llm.invoke(messages)
    return {"result": json.loads(response.content)}


graph = (
    StateGraph(OrchestratorState)
    .add_edge(START, "decompose_query")
    .add_node("decompose_query", decompose_query)
    .add_edge("decompose_query", END)
    .compile()
)


def invoke(context: RequestContext) -> dict:
    state = OrchestratorState(query=context.get_user_input())
    result: OrchestratorState = graph.invoke(state, config={"configurable": {"thread_id": context.context_id}})
    return result["result"]
