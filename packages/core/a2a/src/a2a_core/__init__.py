"""A2A adapter layer (public facade).

Carries typed Pydantic contracts as A2A structured data parts, builds the agent
card and Starlette app, drives the task lifecycle, and provides the typed client.
Capability-agnostic.
"""

from .client import call_agent
from .payloads import (
    JSON_MEDIA_TYPE,
    PayloadContractError,
    message_from_model,
    model_from_message,
    model_from_task,
    part_from_model,
)
from .server import (
    CONTRACT_EXTENSION_URI,
    A2AAgentExecutor,
    build_app,
    build_card,
    serve,
)

__all__ = [
    "CONTRACT_EXTENSION_URI",
    "JSON_MEDIA_TYPE",
    "PayloadContractError",
    "A2AAgentExecutor",
    "build_app",
    "build_card",
    "call_agent",
    "message_from_model",
    "model_from_message",
    "model_from_task",
    "part_from_model",
    "serve",
]
