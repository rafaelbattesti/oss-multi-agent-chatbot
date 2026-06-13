from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette

from bastion.executor import BastionAgentExecutor


def create_agent_card(base_url: str) -> AgentCard:
  skill = AgentSkill(
    id="payload_echo",
    name="Payload Echo",
    description="Returns the A2A payload received by the stub agent.",
    input_modes=["text/plain"],
    output_modes=["application/json"],
    tags=["a2a", "stub"],
    examples=["Show me the payload you received."],
  )

  return AgentCard(
    name="Bastion Stub Agent",
    description="Stub A2A agent that returns the payload it receives.",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    supported_interfaces=[
      AgentInterface(protocol_binding="JSONRPC", url=base_url),
    ],
    skills=[skill],
  )


def create_app(base_url: str) -> Starlette:
  public_agent_card = create_agent_card(base_url)
  request_handler = DefaultRequestHandler(
    agent_executor=BastionAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=public_agent_card,
  )

  routes = []
  routes.extend(create_agent_card_routes(public_agent_card))
  routes.extend(create_jsonrpc_routes(request_handler, "/"))
  return Starlette(routes=routes)


agent_card = create_agent_card("http://127.0.0.1:9999")
app = create_app("http://127.0.0.1:9999")
