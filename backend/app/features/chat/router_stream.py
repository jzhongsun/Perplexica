"""Chat router module."""

import datetime
from typing import Optional
from app.core.ui_message_stream import ErrorUIMessageStreamPart, FinishUIMessageStreamPart, StartUIMessageStreamPart, TextDeltaUIMessageStreamPart, TextEndUIMessageStreamPart, TextStartUIMessageStreamPart
from app.db.schemas import User
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import uuid
from loguru import logger
import traceback

from .service import ChatService
from .schemas import ChatStreamRequest, ChatRequest
from ...core.utils.messages import (
    a2a_message_to_ui_message_stream_parts,
)
from a2a.client import A2AClient
from a2a.types import (
    SendStreamingMessageSuccessResponse,
)
import a2a.types as a2a_types
from app.depends import get_chat_service, get_current_user

router = APIRouter(prefix="/chat-stream", tags=["chat"])

@router.post("", response_class=EventSourceResponse)
async def handle_chat_stream(
    request: ChatStreamRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Create a new chat with streaming response."""
    
    chat_id = request.id
    if chat_id is None or len(chat_id) == 0:
        chat_id = str(uuid.uuid4())
        request.id = chat_id
        chat = await chat_service.create_chat(ChatRequest(
            chatId=chat_id,
            messages=request.messages,
            options=request.options,
            files=request.files,
        ))
    else:
        chat = await chat_service.get_chat(chat_id)
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        
    for message in request.messages:
        if message.id is None or len(message.id) == 0:
            message.id = str(uuid.uuid4())
        if message.metadata is None:
            message.metadata = {}
        if "createdAt" not in message.metadata:
            message.metadata["createdAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    async def event_generator():
        stream = chat_service.chat_stream(chat_id, request.messages, request.options)
        try:
            last_message_id = None
            
            class ActiveMessageProps(BaseModel):
                reference_message_id: Optional[str] = None
                message_id: Optional[str] = None
                text_part_id: Optional[str] = None
                reasoning_part_id: Optional[str] = None

            active_message_props = ActiveMessageProps()
            async for response_item in stream:
                if isinstance(response_item.root, SendStreamingMessageSuccessResponse):
                    logger.info(f"Response item: {type(response_item.root.result)} - {response_item.root.result}")
                    if isinstance(response_item.root.result, a2a_types.Message):
                        pass
                    elif isinstance(response_item.root.result, a2a_types.Task):
                        pass
                    elif isinstance(
                        response_item.root.result, a2a_types.TaskStatusUpdateEvent
                    ):
                        response_message = response_item.root.result.status.message
                        if response_message is None:
                            continue
                        
                        if active_message_props.reference_message_id is None:
                            active_message_props.reference_message_id = response_message.messageId
                            active_message_props.message_id = str(uuid.uuid4())
                            yield {
                                "id": str(uuid.uuid4()),
                                "event": "message",
                                "data": StartUIMessageStreamPart(messageId=active_message_props.message_id).model_dump_json(exclude_none=True),
                            }
                        if active_message_props.reference_message_id != response_message.messageId:
                            assert active_message_props.message_id is not None
                            if active_message_props.text_part_id is not None:
                                yield {
                                    "id": str(uuid.uuid4()),
                                    "event": "message",
                                    "data": TextEndUIMessageStreamPart(id=active_message_props.text_part_id).model_dump_json(exclude_none=True),
                                }
                                active_message_props.text_part_id = None

                            # previous message is finished, start a new one
                            yield {
                                "id": str(uuid.uuid4()),
                                "event": "message",
                                "data": FinishUIMessageStreamPart(messageId=active_message_props.message_id).model_dump_json(exclude_none=True),
                            }
                            active_message_props.reference_message_id = response_message.messageId
                            active_message_props.message_id = str(uuid.uuid4())
                            yield {
                                "id": str(uuid.uuid4()),
                                "event": "message",
                                "data": StartUIMessageStreamPart(messageId=active_message_props.message_id).model_dump_json(exclude_none=True),
                            }
                        assert active_message_props.message_id is not None
                        for part in response_message.parts:
                            if isinstance(part.root, a2a_types.TextPart):
                                if active_message_props.text_part_id is None:
                                    active_message_props.text_part_id = str(uuid.uuid4())
                                    yield {
                                        "id": str(uuid.uuid4()),
                                        "event": "message",
                                        "data": TextStartUIMessageStreamPart(id=active_message_props.text_part_id).model_dump_json(exclude_none=True),
                                    }
                                if part.root.text is not None:
                                    yield {
                                        "id": str(uuid.uuid4()),
                                        "event": "message",
                                        "data": TextDeltaUIMessageStreamPart(id=active_message_props.text_part_id, delta=part.root.text).model_dump_json(exclude_none=True),
                                    }
                            elif isinstance(part.root, a2a_types.DataPart):
                                logger.info(f"Data part: {part.root}")
                            elif isinstance(part.root, a2a_types.FilePart):
                                logger.info(f"File part: {part.root}")
                            else:
                                logger.info(f"Unknown part: {part.root}")
                                
                    elif isinstance(
                        response_item.root.result, a2a_types.TaskArtifactUpdateEvent
                    ):
                        pass
                    else:
                        raise ValueError(
                            f"Unsupported response item type: {type(response_item.root.result)}"
                        )

            if active_message_props.text_part_id is not None:
                yield {
                    "id": str(uuid.uuid4()),
                    "event": "message",
                    "data": TextEndUIMessageStreamPart(id=active_message_props.text_part_id).model_dump_json(exclude_none=True),
                }
                active_message_props.text_part_id = None
            if active_message_props.message_id is not None:
                yield {
                    "id": str(uuid.uuid4()),
                    "event": "message",
                    "data": FinishUIMessageStreamPart(messageId=active_message_props.message_id).model_dump_json(exclude_none=True),
                }
                active_message_props.message_id = None
                active_message_props.reference_message_id = None
        except Exception as e:
            error_msg = f"Error in chat stream: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            logger.error(error_msg)
            yield {
                "id": str(uuid.uuid4()),
                "event": "message",
                "data": ErrorUIMessageStreamPart(errorText=str(e)).model_dump_json(exclude_none=True),
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
