from typing import AsyncIterable
import uuid

from semantic_kernel.agents import AgentResponseItem
from semantic_kernel.contents import ChatMessageContent, StreamingChatMessageContent, TextContent

from ..ui_messages import UIMessage, TextUIPart

def ui_message_to_sk_chat_message_content(ui_message: UIMessage) -> ChatMessageContent:
    return ChatMessageContent(
        role=ui_message.role,
        items=[
            TextContent(text=ui_message.parts[0].text)
        ]
    )

def sk_agent_response_item_to_ui_message(response_item: AgentResponseItem) -> UIMessage:
    return UIMessage(
        id=str(uuid.uuid4()),
        role=response_item.role,
        parts=[
            TextUIPart(text=f"{response_item}", type="text")
        ],
    )

async def sk_agent_response_stream_to_ui_message_stream(agent_response_stream: AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]) -> AsyncIterable[UIMessage]:
    async for response_item in agent_response_stream:
        yield sk_agent_response_item_to_ui_message(response_item)
