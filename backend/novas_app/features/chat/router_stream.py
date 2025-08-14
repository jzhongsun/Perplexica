"""Chat router module."""

import datetime
import asyncio
from typing import Dict, Any
from novas_app.core.ui_message_stream import ErrorUIMessageStreamPart
from novas_app.db.schemas import User
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uuid
from loguru import logger
from novas_app.core.stream_manager import get_stream_manager

from .service import ChatService
from .schemas import ChatStreamRequest, ChatRequest
from novas_app.depends import get_chat_service, get_current_user

router = APIRouter(prefix="/chat-stream", tags=["chat"])

async def chat_producer(stream_key: str, chat_service: ChatService, chat_id: str, messages, options: Dict[str, Any]):
    """Producer function that generates chat stream data."""
    stream_manager = get_stream_manager()
    
    try:
        # Start the actual chat stream
        stream = chat_service.chat_stream(chat_id, messages, options)
        async for stream_part in stream:
            # Write each stream part to Redis Stream
            await stream_manager.publish_to_stream(
                stream_key,
                "stream_part",
                {
                    "data": stream_part.model_dump_json(exclude_none=True)
                }
            )
    except Exception as e:
        logger.error(f"Error in chat producer: {str(e)}")
        # Error will be handled by the stream manager
        raise

@router.post("", response_class=EventSourceResponse)
async def handle_chat_stream(
    request: ChatStreamRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Create a new chat with streaming response using Redis Stream."""
    
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

    stream_manager = get_stream_manager()
    
    async def event_generator():
        """Generate SSE events from Redis Stream."""
        # Create stream and get consumer
        stream_key = await stream_manager.create_stream(chat_id)
        consumer_id = await stream_manager.add_consumer(stream_key)
        
        try:
            # Start producer if not already running
            producer_started = await stream_manager.start_producer(
                stream_key,
                chat_producer,
                chat_service,
                chat_id,
                request.messages,
                request.options.__dict__ if request.options else {}
            )
            
            if producer_started:
                logger.info(f"Started producer for stream {stream_key}")
            else:
                logger.info(f"Producer already running for stream {stream_key}")
            
            # Consume from stream
            async for event in stream_manager.consume_stream(stream_key, consumer_id):
                yield event
                
        except asyncio.CancelledError:
            logger.info(f"Consumer {consumer_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in event generator: {str(e)}")
            yield {
                "id": str(uuid.uuid4()),
                "event": "message",
                "data": ErrorUIMessageStreamPart(errorText=str(e)).model_dump_json(exclude_none=True),
            }
        finally:
            # Clean up consumer
            await stream_manager.remove_consumer(stream_key, consumer_id)

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
