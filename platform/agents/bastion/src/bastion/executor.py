from typing import Any

from a2a.helpers import new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types.a2a_pb2 import TaskState
from google.protobuf.json_format import MessageToDict

from bastion.graph import run_stub_graph


def _serialize_payload(payload: Any) -> dict[str, Any]:
  if hasattr(payload, "model_dump"):
    return payload.model_dump(mode="json", by_alias=True)

  if hasattr(payload, "dict"):
    return payload.dict()

  return MessageToDict(payload, preserving_proto_field_name=True)


def build_response_message_text(payload: dict[str, Any]) -> str:
  return run_stub_graph(payload)["response_text"]


class BastionAgentExecutor(AgentExecutor):
  async def execute(
    self,
    context: RequestContext,
    event_queue: EventQueue,
  ) -> None:
    if context.current_task:
      task = context.current_task
    else:
      task = new_task_from_user_message(context.message)
      await event_queue.enqueue_event(task)

    task_updater = TaskUpdater(
      event_queue=event_queue,
      task_id=task.id,
      context_id=task.context_id,
    )

    await task_updater.update_status(
      state=TaskState.TASK_STATE_WORKING,
      message=new_text_message("Processing request payload."),
    )

    response_text = build_response_message_text(_serialize_payload(context.message))

    await task_updater.add_artifact(
      parts=[new_text_part(text=response_text, media_type="application/json")],
    )
    await task_updater.update_status(
      state=TaskState.TASK_STATE_COMPLETED,
      message=new_text_message(response_text),
    )

  async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
    raise NotImplementedError("Cancel is not supported.")
