import json
import uuid
import traceback
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
    DataPart,
)
from a2a.utils import new_task
from loguru import logger

from semantic_kernel.contents import AuthorRole
from semantic_kernel.agents import Agent, AgentThread, AgentResponseItem
from semantic_kernel.contents import (
    ChatMessageContent,
    TextContent,
    StreamingChatMessageContent,
    StreamingTextContent,
    FunctionCallContent,
    FunctionResultContent,
)
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES


def sk_item_to_a2a_part(item: CMC_ITEM_TYPES) -> Part:
    if isinstance(item, TextContent):
        return Part(root=TextPart(text=item.text))
    elif isinstance(item, FunctionCallContent):
        arguments = {}
        if isinstance(item.arguments, dict):
            arguments = item.arguments
        elif isinstance(item.arguments, str):
            arguments = json.loads(item.arguments)
        else:
            arguments = {}
            
        return Part(
            root=DataPart(
                data={
                    "id": item.id,
                    "tool_call_id": item.call_id if item.call_id else item.id,
                    "tool_name": item.name,
                    "arguments": arguments,
                },
                metadata={"inner_part_type": "tool_call"},
            )
        )
    elif isinstance(item, FunctionResultContent):
        return Part(
            root=DataPart(
                data={
                    "id": item.id,
                    "tool_call_id": item.call_id if item.call_id else item.id,
                    "tool_name": item.name,
                    "result": item.result,
                },
                metadata={"inner_part_type": "tool_result"},
            )
        )
    else:
        logger.warning(f"Unsupported item type: {type(item)}")
        return Part(
            root=TextPart(
                text=f"Unsupported item type: {type(item)}: {item.model_dump_json(exclude_none=True)}"
            )
        )


def sk_message_to_a2a_message(
    message: StreamingChatMessageContent,
    message_id: str | None = None,
    contextId: str | None = None,
    taskId: str | None = None,
) -> tuple[Message, str]:
    if message_id is None:
        message_id = (
            message.metadata["id"] if "id" in message.metadata else str(uuid.uuid4())
        )
    else:
        if (
            message.metadata
            and "id" in message.metadata
            and message_id != message.metadata["id"]
        ):
            logger.warning(
                f"Message ID mismatch: {message_id} != {message.metadata['id']}"
            )

    return (
        Message(
            contextId=contextId,
            taskId=taskId,
            messageId=message_id,
            metadata=message.metadata,
            parts=[sk_item_to_a2a_part(item) for item in message.items],
            role=Role.user if message.role == AuthorRole.USER else Role.agent,
        ),
        message_id,
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
        agent_name: str,
        agent_card: AgentCard,
        agent_config: Dict[str, Any],
        agent_builder: Callable[[str, AgentCard, Dict[str, Any]], Agent],
    ):
        self.agent_name = agent_name
        self.agent_card = agent_card
        self.agent_config = agent_config
        self.agent_builder = agent_builder

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        input_message = context.message
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        task_updater = TaskUpdater(event_queue, task.id, task.contextId)

        agent = self.agent_builder(self.agent_name, self.agent_card, self.agent_config)
        logger.info(f"Agent created: {agent} - type: {type(agent)}")
        thread: AgentThread | None = None

        try:
            messages = [a2a_message_to_sk_message(input_message)]
            await task_updater.submit()

            stream = agent.invoke_stream(messages=messages, thread=thread)
            await task_updater.start_work()

            response_message_chunks: list[StreamingChatMessageContent] = []
            previous_message_id = None
            async for partial in stream:
                response_item: AgentResponseItem[StreamingChatMessageContent] = partial
                thread = response_item.thread
                response_message: StreamingChatMessageContent = response_item.message
                if any(
                    isinstance(i, StreamingTextContent) for i in response_message.items
                ):
                    response_message_chunks.append(response_message)

                # logger.debug(f"Response item: {response_item.model_dump(exclude={'thread'})}")
                message_id = (
                    response_message.metadata["id"]
                    if "id" in response_message.metadata
                    else str(uuid.uuid4())
                )
                if previous_message_id != message_id:
                    previous_message_id = message_id
                a2a_message, message_id = sk_message_to_a2a_message(
                    response_message, previous_message_id, task.contextId, task.id
                )
                previous_message_id = message_id
                await task_updater.update_status(TaskState.working, message=a2a_message)

            await task_updater.complete()
        except Exception as e:
            logger.error(f"Error in agent execution: {e}, {traceback.format_exc()}")
            await task_updater.failed()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
