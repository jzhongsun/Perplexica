import uuid
from typing import Any, Callable, Dict

from a2a.server.tasks import TaskUpdater
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCard,
    Message,
    Part,
    TextPart,
    TaskState,
    Role,
)
from a2a.utils import new_task
from loguru import logger

from semantic_kernel.contents import AuthorRole
from semantic_kernel.agents import Agent, AgentThread, AgentResponseItem
from semantic_kernel.contents import ChatMessageContent, TextContent, StreamingChatMessageContent
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES

def sk_item_to_a2a_part(item: CMC_ITEM_TYPES) -> Part:
    if isinstance(item, TextContent):
        return Part(root=TextPart(text=item.text))
    else:
        raise ValueError(f"Unsupported item type: {type(item)}")

def sk_message_to_a2a_message(message: StreamingChatMessageContent, contextId: str, taskId: str) -> Message:
    return Message(
        contextId=contextId,
        taskId=taskId,
        messageId=message.metadata["id"] if "id" in message.metadata else str(uuid.uuid4()),
        metadata=message.metadata,
        parts=[
            sk_item_to_a2a_part(item)
            for item in message.items
        ],
        role=Role.user if message.role == AuthorRole.USER else Role.agent,
    )


def a2a_part_to_sk_item(part: Part) -> CMC_ITEM_TYPES:
    if isinstance(part.root, TextPart):
        return TextContent(text=part.root.text)
    else:
        raise ValueError(f"Unsupported part type: {type(part.root)}")


def a2a_message_to_sk_message(message: Message) -> ChatMessageContent:
    return ChatMessageContent(
        role=message.role,
        items=[a2a_part_to_sk_item(part) for part in message.parts],
    )


class SemanticKernelAgentExecutor(AgentExecutor):
    def __init__(
        self,
        agent_card: AgentCard,
        agent_builder: Callable[[AgentCard, Dict[str, Any]], Agent],
    ):
        self.agent_card = agent_card
        self.agent_builder = agent_builder

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        message = context.message
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        task_updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        agent = self.agent_builder(self.agent_card, task.metadata)
        thread: AgentThread | None = None
        await task_updater.start_work()
        async for partial in agent.invoke_stream(
            messages=a2a_message_to_sk_message(message), thread=thread
        ):
            response_item : AgentResponseItem[StreamingChatMessageContent] = partial
            thread = response_item.thread
            response_message : StreamingChatMessageContent = response_item.message

            logger.debug(f"Response item: {response_item.model_dump(exclude={'thread'})}")
            await task_updater.update_status(TaskState.working, message=sk_message_to_a2a_message(response_message, task.contextId, task.id))
            
        await task_updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
