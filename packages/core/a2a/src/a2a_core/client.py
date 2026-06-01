"""A2A client helper for typed structured payload contracts."""

from __future__ import annotations

import logging
from typing import TypeVar
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Role, SendMessageRequest
from a2a.utils import TransportProtocol
from pydantic import BaseModel

from .a2a_payloads import PayloadContractError, message_from_model, model_from_message

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


async def call_agent(
    base_url: str, payload: BaseModel, response_model: type[T], timeout: float = 300.0
) -> T:
    message_id = uuid4().hex
    request_model = payload.__class__.__name__
    response_name = response_model.__name__
    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            client_config = ClientConfig(
                streaming=False,
                supported_protocol_bindings=[TransportProtocol.JSONRPC],
                httpx_client=http_client,
            )
            client = await create_client(base_url, client_config)
            request = SendMessageRequest(
                message=message_from_model(payload, role=Role.ROLE_USER)
            )
            request.message.message_id = message_id
            logger.info(
                "Starting A2A call to %s with %s, expecting %s (message_id=%s).",
                base_url,
                request_model,
                response_name,
                message_id,
            )
            message: Message | None = None
            async for response in client.send_message(request):
                if response.WhichOneof("payload") == "message":
                    message = response.message
    except Exception:
        logger.exception(
            "A2A call to %s failed while sending %s and expecting %s "
            "(message_id=%s).",
            base_url,
            request_model,
            response_name,
            message_id,
        )
        raise

    if message is None:
        logger.error(
            "A2A call to %s returned no message while expecting %s "
            "(message_id=%s).",
            base_url,
            response_name,
            message_id,
        )
        raise RuntimeError("A2A peer returned no message response")
    try:
        result = model_from_message(message, response_model)
    except PayloadContractError as exc:
        logger.error(
            "A2A call to %s returned an invalid %s payload: %s (message_id=%s).",
            base_url,
            response_name,
            exc,
            message_id,
            exc_info=True,
        )
        raise RuntimeError(f"A2A peer returned invalid payload: {exc}") from exc
    logger.info(
        "Completed A2A call to %s with %s (message_id=%s).",
        base_url,
        response_name,
        message_id,
    )
    return result
