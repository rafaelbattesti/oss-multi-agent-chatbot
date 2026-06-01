"""A2A server scaffolding: agent-card builder, task-lifecycle executor, app/serve.

The executor implements the SDK ``AgentExecutor`` ABC and acts as the bridge
between the A2A protocol and the agent's business logic: it drives the task
lifecycle (working -> artifact -> completed) and calls the injected business
logic, which maps the typed request to a typed response.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Sequence

import config
import uvicorn
from a2a.helpers.proto_helpers import new_task_from_user_message, new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from a2a.utils import DEFAULT_RPC_URL, TransportProtocol
from a2a.utils.errors import UnsupportedOperationError
from google.protobuf import struct_pb2
from google.protobuf.json_format import ParseDict
from observability import configure_logging
from pydantic import BaseModel
from starlette.applications import Starlette

from .payloads import (
    JSON_MEDIA_TYPE,
    contract_extension_params,
    contract_tags,
    model_from_message,
    part_from_model,
)

CONTRACT_EXTENSION_URI = "urn:thesis:a2a:contract"

# The agent's business logic: map a typed request to a typed response.
Invoke = Callable[[BaseModel], Awaitable[BaseModel]]


def _struct(value: dict) -> struct_pb2.Struct:
    return ParseDict(value, struct_pb2.Struct())


def build_card(
    *,
    name: str,
    description: str,
    skill_id: str,
    public_url: str,
    input_model: type[BaseModel],
    output_model: type[BaseModel],
    semantic_tags: Sequence[str],
    version: str = "0.1.0",
) -> AgentCard:
    tags = list(semantic_tags) + contract_tags(input_model, output_model)
    return AgentCard(
        name=name,
        description=description,
        version=version,
        capabilities=AgentCapabilities(
            streaming=False,
            extensions=[
                AgentExtension(
                    uri=CONTRACT_EXTENSION_URI,
                    description="Typed A2A payload contract for this agent skill.",
                    required=False,
                    params=_struct(contract_extension_params(input_model, output_model)),
                )
            ],
        ),
        default_input_modes=[JSON_MEDIA_TYPE],
        default_output_modes=[JSON_MEDIA_TYPE],
        skills=[
            AgentSkill(
                id=skill_id,
                name=name,
                description=description,
                tags=tags,
                input_modes=[JSON_MEDIA_TYPE],
                output_modes=[JSON_MEDIA_TYPE],
            )
        ],
        supported_interfaces=[
            AgentInterface(protocol_binding=TransportProtocol.JSONRPC, url=public_url)
        ],
    )


class A2AAgentExecutor(AgentExecutor):
    """Bridge between the A2A protocol and an agent's business logic."""

    def __init__(self, invoke: Invoke, *, request_model: type[BaseModel]) -> None:
        self._invoke = invoke
        self._request_model = request_model

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # 1. Collect a task from request context, creating one if absent.
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        # 2. Mark the task working.
        task_updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await task_updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing request..."),
        )

        # 3. Decode the typed request and invoke the business logic.
        request = model_from_message(context.message, self._request_model)
        response = await self._invoke(request)

        # 4. Emit the typed response as an artifact.
        await task_updater.add_artifact(parts=[part_from_model(response)])

        # 5. Mark the task completed.
        await task_updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Request is completed!"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise UnsupportedOperationError("This agent does not support cancellation.")


def build_app(card: AgentCard, invoke: Invoke, *, request_model: type[BaseModel]):
    request_handler = DefaultRequestHandler(
        agent_executor=A2AAgentExecutor(invoke, request_model=request_model),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(
        request_handler, DEFAULT_RPC_URL
    )
    return Starlette(routes=routes)


def serve(card: AgentCard, invoke: Invoke, *, request_model: type[BaseModel]) -> None:
    configure_logging()
    uvicorn.run(
        build_app(card, invoke, request_model=request_model),
        host="0.0.0.0",
        port=config.PORT,
    )
