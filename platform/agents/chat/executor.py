from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types.a2a_pb2 import TaskState, TaskStatus, TaskStatusUpdateEvent
from a2a.helpers import new_task_from_user_message, new_data_artifact_update_event

from skills.decompose_query import decompose_query_skill
from graph import invoke


class ChatAgentExecutor(AgentExecutor):

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        await event_queue.enqueue_event(task)

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        result = invoke(context)

        await event_queue.enqueue_event(
            new_data_artifact_update_event(
                task_id=task.id,
                context_id=task.context_id,
                name=decompose_query_skill.id,
                data=result,
                media_type='application/json',
            )
        )

        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task.id,
                context_id=task.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
            )
        )
