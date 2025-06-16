"""Chat router module."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import httpx
from sse_starlette.sse import EventSourceResponse
import uuid
import json
from loguru import logger
from typing import AsyncGenerator

from .service import ChatService
from .schemas import ChatRequest
from ...core.ui_messages import UIMessage, TextUIPart
from ...core.utils.messages import (
    a2a_message_to_ui_message,
)
from a2a.client import A2AClient
from a2a.types import (
    SendStreamingMessageRequest,
    SendStreamingMessageSuccessResponse,
    MessageSendParams,
    TextPart,
    Role,
)
import a2a.types as a2a_types

router = APIRouter(prefix="/chat-stream", tags=["chat"])


async def error_event_generator(error_message: str) -> AsyncGenerator[str, None]:
    error_ui_message = UIMessage(
        id=str(uuid.uuid4()),
        parts=[TextUIPart(text=f"Error: {error_message}")],
        role="assistant",
        error=True,
    )
    yield error_ui_message.model_dump_json()


async def resolve_agent_client(request: ChatRequest) -> A2AClient:
    a2a_client = A2AClient(
        httpx_client=httpx.AsyncClient(),
        url="http://localhost:10010/web_search/",
    )
    return a2a_client


@router.post("", response_class=EventSourceResponse)
async def handle_chat_stream(
    request: ChatRequest, chat_service: ChatService = Depends(ChatService)
) -> StreamingResponse:
    """Create a new chat with streaming response."""

    async def event_generator():
        message_id = str(uuid.uuid4())
        agent_client = await resolve_agent_client(request)
        stream = agent_client.send_message_streaming(
            request=SendStreamingMessageRequest(
                id=str(uuid.uuid4()),
                params=MessageSendParams(
                    message=a2a_types.Message(
                        messageId=message_id,
                        role=Role.user,
                        parts=[
                            TextPart(text=message.parts[0].text)
                            for message in request.messages
                        ],
                    ),
                    metadata={},
                ),
            )
        )
        yield {
            "id": str(uuid.uuid4()),
            "event": "message",
            "data": json.dumps(
                {"type": "start", "messageId": message_id, "messageMetadata": {}},
                ensure_ascii=False,
            ),
        }
        try:
            async for response_item in stream:
                response_item_ui_message = None
                if isinstance(response_item.root, SendStreamingMessageSuccessResponse):
                    logger.info(f"Response item: {response_item.root.result}")
                    if isinstance(response_item.root.result, a2a_types.Message):
                        response_item_ui_message = a2a_message_to_ui_message(
                            response_item.root.result
                        )
                    elif isinstance(response_item.root.result, a2a_types.Task):
                        pass
                    elif isinstance(
                        response_item.root.result, a2a_types.TaskStatusUpdateEvent
                    ):
                        response_message = response_item.root.result.status.message
                        if response_message is not None:
                            response_item_ui_message = a2a_message_to_ui_message(
                                response_message
                            )
                    elif isinstance(
                        response_item.root.result, a2a_types.TaskArtifactUpdateEvent
                    ):
                        pass
                    else:
                        raise ValueError(
                            f"Unsupported response item type: {type(response_item.root.result)}"
                        )

                if response_item_ui_message is None:
                    continue
                for part in response_item_ui_message.parts:
                    yield {
                        "id": str(uuid.uuid4()),
                        "event": "message",
                        "data": json.dumps(part.model_dump(), ensure_ascii=False),
                    }
        except Exception as e:
            logger.error(f"Error in chat stream: {str(e)}")
            async for error_message in error_event_generator(str(e)):
                yield error_message
            return

        yield {
            "id": str(uuid.uuid4()),
            "event": "message",
            "data": json.dumps(
                {"type": "finish", "messageId": message_id, "messageMetadata": {}},
                ensure_ascii=False,
            ),
        }

    return EventSourceResponse(
        event_generator(),
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
