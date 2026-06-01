"""Helpers for carrying typed contracts in A2A structured data parts."""

from __future__ import annotations

from typing import TypeVar

from a2a.helpers.proto_helpers import get_data_parts, new_data_message
from a2a.types import Message, Role
from pydantic import BaseModel, ValidationError

from .schemas import CONTRACT_VERSION

JSON_MEDIA_TYPE = "application/json"

T = TypeVar("T", bound=BaseModel)


class PayloadContractError(ValueError):
    """Raised when an A2A message does not match the expected payload contract."""

    def __init__(self, message: str, data: dict | None = None) -> None:
        self.data = data
        super().__init__(message)


def message_from_model(
    payload: BaseModel,
    *,
    role: Role,
    context_id: str | None = None,
    task_id: str | None = None,
) -> Message:
    return new_data_message(
        payload.model_dump(mode="json"),
        media_type=JSON_MEDIA_TYPE,
        context_id=context_id,
        task_id=task_id,
        role=role,
    )


def model_from_message(message: Message | None, model: type[T]) -> T:
    if message is None:
        raise PayloadContractError(f"Expected {model.__name__} message, got no message")

    parts = get_data_parts(message.parts)
    if len(parts) != 1:
        raise PayloadContractError(
            f"Expected exactly one {JSON_MEDIA_TYPE} data part for {model.__name__}",
            data={"data_part_count": len(parts)},
        )

    payload = parts[0]
    if not isinstance(payload, dict):
        raise PayloadContractError(
            f"Expected {model.__name__} data part to contain a JSON object",
            data={"payload_type": type(payload).__name__},
        )

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise PayloadContractError(
            f"Invalid {model.__name__} payload", data={"errors": exc.errors()}
        ) from exc


def contract_tags(input_model: type[BaseModel], output_model: type[BaseModel]) -> list[str]:
    return [
        f"contract:{CONTRACT_VERSION}",
        f"input:{input_model.__name__}",
        f"output:{output_model.__name__}",
    ]


def contract_extension_params(
    input_model: type[BaseModel], output_model: type[BaseModel]
) -> dict:
    return {
        "contract_version": CONTRACT_VERSION,
        "input": {
            "name": input_model.__name__,
            "media_type": JSON_MEDIA_TYPE,
            "json_schema": input_model.model_json_schema(),
        },
        "output": {
            "name": output_model.__name__,
            "media_type": JSON_MEDIA_TYPE,
            "json_schema": output_model.model_json_schema(),
        },
    }
