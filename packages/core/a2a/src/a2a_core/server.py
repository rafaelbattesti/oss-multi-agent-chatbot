"""Minimal A2A server scaffolding shared by every agent.

An agent supplies an async typed handler; this module wraps it in an A2A
``AgentExecutor`` that carries Pydantic contracts as structured data parts.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Sequence

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentExtension,
    AgentInterface,
    AgentSkill,
    Role,
)
from a2a.utils.errors import InvalidAgentResponseError, InvalidParamsError
from a2a.utils import DEFAULT_RPC_URL, TransportProtocol
from google.protobuf import struct_pb2
from google.protobuf.json_format import ParseDict
from pydantic import BaseModel, ValidationError
from starlette.applications import Starlette

from . import config
from .a2a_payloads import (
    JSON_MEDIA_TYPE,
    PayloadContractError,
    contract_extension_params,
    contract_tags,
    message_from_model,
    model_from_message,
)
from .log_config import configure_logging

Handler = Callable[[BaseModel], Awaitable[BaseModel | dict]]
logger = logging.getLogger(__name__)

CONTRACT_EXTENSION_URI = "urn:thesis:a2a:contract"


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


class _StructuredExecutor(AgentExecutor):
    def __init__(
        self,
        handler: Handler,
        agent_name: str,
        request_model: type[BaseModel],
        response_model: type[BaseModel],
    ) -> None:
        self._handler = handler
        self._agent_name = agent_name
        self._request_model = request_model
        self._response_model = response_model

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            payload = model_from_message(context.message, self._request_model)
        except PayloadContractError as exc:
            logger.warning(
                "%s rejected an invalid %s request for task %s in context %s: %s.",
                self._agent_name,
                self._request_model.__name__,
                context.task_id,
                context.context_id,
                str(exc),
                exc_info=True,
            )
            raise InvalidParamsError(message=str(exc), data=exc.data) from exc

        logger.info(
            "%s accepted a %s request for task %s in context %s.",
            self._agent_name,
            self._request_model.__name__,
            context.task_id,
            context.context_id,
        )
        try:
            result = await self._handler(payload)
        except Exception:
            logger.exception(
                "%s failed while handling %s and preparing %s for task %s "
                "in context %s.",
                self._agent_name,
                self._request_model.__name__,
                self._response_model.__name__,
                context.task_id,
                context.context_id,
            )
            raise

        try:
            if isinstance(result, self._response_model):
                response = result
            elif isinstance(result, BaseModel):
                response = self._response_model.model_validate(result.model_dump())
            else:
                response = self._response_model.model_validate(result)
        except ValidationError as exc:
            logger.error(
                "%s produced an invalid %s response for task %s in context %s.",
                self._agent_name,
                self._response_model.__name__,
                context.task_id,
                context.context_id,
                exc_info=True,
            )
            raise InvalidAgentResponseError(
                message=f"Handler returned invalid {self._response_model.__name__}",
                data={"errors": exc.errors()},
            ) from exc

        logger.info(
            "%s produced a valid %s response for task %s in context %s.",
            self._agent_name,
            self._response_model.__name__,
            context.task_id,
            context.context_id,
        )
        message = message_from_model(
            response,
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(message)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancellation is not supported in the MVP")


def build_app(
    card: AgentCard,
    handler: Handler,
    *,
    request_model: type[BaseModel],
    response_model: type[BaseModel],
):
    request_handler = DefaultRequestHandler(
        agent_executor=_StructuredExecutor(
            handler, card.name, request_model, response_model
        ),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(
        request_handler, DEFAULT_RPC_URL
    )
    return Starlette(routes=routes)


def serve(
    card: AgentCard,
    handler: Handler,
    *,
    request_model: type[BaseModel],
    response_model: type[BaseModel],
) -> None:
    configure_logging()
    uvicorn.run(
        build_app(
            card,
            handler,
            request_model=request_model,
            response_model=response_model,
        ),
        host="0.0.0.0",
        port=config.PORT,
    )
