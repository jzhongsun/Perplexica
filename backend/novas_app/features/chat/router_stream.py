"""Chat router module."""

import datetime
import asyncio
import uuid
from loguru import logger
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from novas_app.core.ui_message_stream import ErrorUIMessageStreamPart
from novas_app.db.schemas import User

from .service import ChatService
from .schemas import ChatStreamRequest, ChatRequest
from novas_app.depends import get_chat_service, get_current_user


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
        
    # Ensure message IDs and metadata are set
    for message in request.messages:
        if message.id is None or len(message.id) == 0:
            message.id = str(uuid.uuid4())
        if message.metadata is None:
            message.metadata = {}
        if "createdAt" not in message.metadata:
            message.metadata["createdAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    async def event_generator():
        """Generate SSE events directly from chat stream."""
        try:
            # Get the chat stream directly from service
            options = request.options.__dict__ if request.options else {}
            stream = chat_service.chat_stream(chat_id, request.messages, options)
            
            # Stream each part as SSE event
            async for stream_part in stream:
                # print(f'stream_part: {stream_part}')
                yield {
                    "id": str(uuid.uuid4()),
                    "event": "message",
                    "data": stream_part.model_dump_json(exclude_none=True),
                }
                
        except asyncio.CancelledError as e:
            # Client disconnected - this is normal, log as info without full traceback
            logger.info(f"Chat stream cancelled for chat {chat_id} (client disconnected)")
            logger.error(f"chat stream cancelled: {chat_id} {e}, {traceback.format_exc()}")
            
            raise
        except Exception as e:
            logger.error(f"chat stream error: {e}, {traceback.format_exc()}")

            yield {
                "id": str(uuid.uuid4()),
                "event": "error",
                "data": ErrorUIMessageStreamPart(errorText=str(e)).model_dump_json(exclude_none=True),
            }

    async def client_close_handler(message: any):
        """Handle client close event."""
        logger.warning(f"Client closed chat stream for chat {chat_id} - {message}")
        print(f'{__file__} client_close_handler>\n{message}')

    return EventSourceResponse(
        event_generator(),
        ping=15,  # Send ping every 15 seconds (default)
        headers={
            "x-vercel-ai-ui-message-stream": "v1",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
        client_close_handler_callable=client_close_handler,
    )
