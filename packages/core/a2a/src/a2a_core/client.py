"""A2A client: send a typed request and return the peer's terminal-task artifact.

Consumes the (non-streaming) response stream to its terminal ``Task`` and reads
the typed contract from the task's data artifact. Surfaces a failed/rejected/
canceled task as an error rather than masking it.
"""

from __future__ import annotations

import logging
from typing import TypeVar
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_message_text
from a2a.types import Message, Role, SendMessageRequest, Task, TaskState
from a2a.utils import TransportProtocol
from pydantic import BaseModel

from .payloads import (
    PayloadContractError,
    message_from_model,
    model_from_message,
    model_from_task,
)

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

_TERMINAL_FAILURES = frozenset(
    {
        TaskState.TASK_STATE_FAILED,
        TaskState.TASK_STATE_REJECTED,
        TaskState.TASK_STATE_CANCELED,
    }
)


async def call_agent(
    base_url: str, payload: BaseModel, response_model: type[T], timeout: float = 300.0
) -> T:
    message_id = uuid4().hex
    request_name = payload.__class__.__name__
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
                request_name,
                response_name,
                message_id,
            )
            task: Task | None = None
            message: Message | None = None
            async for response in client.send_message(request):
                kind = response.WhichOneof("payload")
                if kind == "task":
                    task = response.task
                elif kind == "message":
                    message = response.message
    except Exception:
        logger.exception(
            "A2A call to %s failed while sending %s and expecting %s (message_id=%s).",
            base_url,
            request_name,
            response_name,
            message_id,
        )
        raise

    if task is not None:
        state = task.status.state
        if state in _TERMINAL_FAILURES:
            detail = get_message_text(task.status.message)
            logger.error(
                "A2A call to %s ended %s while expecting %s: %s (message_id=%s).",
                base_url,
                TaskState.Name(state),
                response_name,
                detail,
                message_id,
            )
            raise RuntimeError(
                f"A2A peer task {TaskState.Name(state)}: {detail or 'no detail'}"
            )
        payload_source: Task | Message = task
    elif message is not None:
        payload_source = message
    else:
        logger.error(
            "A2A call to %s returned neither task nor message while expecting %s "
            "(message_id=%s).",
            base_url,
            response_name,
            message_id,
        )
        raise RuntimeError("A2A peer returned neither task nor message")

    try:
        result = (
            model_from_task(payload_source, response_model)
            if isinstance(payload_source, Task)
            else model_from_message(payload_source, response_model)
        )
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
