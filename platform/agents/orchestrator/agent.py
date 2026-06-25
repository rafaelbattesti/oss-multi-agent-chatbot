from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

root_agent = Agent(
    model=LiteLlm(model="ollama_chat/gemma4:latest"),
    name="orchestrator",
    description=(
        "Orchestration agent inspects incoming queries, classify and plan the goal workflow before handing off to downstream agents."
    ),
    instruction="""
      You classify incoming queries according to the following schema.
      {
        'type': 'object',
            'properties': {
                'intent':      {'type': 'string'},
                'subject':     {'type': 'string'},
                'entities':    {'type': 'array', 'items': {'type': 'string'}},
                'complexity':  {'type': 'string', 'enum': ['simple', 'medium', 'complex']},
                'sub_queries': {'type': 'array', 'items': {'type': 'string'}},
            },
        'required': ['intent', 'subject', 'entities', 'complexity', 'sub_queries'],
      }
    """,
)