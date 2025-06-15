"""Chat router module."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uuid
import os
import json
import logging
from typing import AsyncGenerator

from .service import ChatService
from .schemas import ChatRequest
from ...core.ui_messages import UIMessage, TextUIPart
from ...core.utils.messages import sk_agent_response_item_to_ui_message, sk_agent_response_stream_to_ui_message_stream

router = APIRouter(prefix="/chat-stream", tags=["chat"])

logger = logging.getLogger(__name__)

async def error_event_generator(error_message: str) -> AsyncGenerator[str, None]:
    error_ui_message = UIMessage(
        id=str(uuid.uuid4()),
        parts=[TextUIPart(text=f"Error: {error_message}")],
        role="assistant",
        error=True
    )
    yield error_ui_message.model_dump_json()

@router.post("", response_class=EventSourceResponse)
async def handle_chat_stream(
    request: ChatRequest, chat_service: ChatService = Depends(ChatService)
) -> StreamingResponse:
    """Create a new chat with streaming response."""

    from semantic_kernel.connectors.ai.open_ai import (
        OpenAIChatCompletion,
        OpenAIPromptExecutionSettings,
    )
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.agents import ChatCompletionAgent

    async def event_generator():
        try:
            # Generate a unique message ID
            message_id = str(uuid.uuid4())
            
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY is not set")
                
            chat_completion = OpenAIChatCompletion(
                api_key=os.getenv("OPENAI_API_KEY"),
                ai_model_id=os.getenv("OPENAI_MODEL_NAME"),
            )
            agent = ChatCompletionAgent(service=chat_completion)
            stream = agent.invoke_stream(
                messages=[
                    ChatMessageContent(role=message.role, content=message.parts[0].text)
                    for message in request.messages
                ]
            )
            yield {
                "id": str(uuid.uuid4()),
                "event": "message",
                "data": json.dumps({
                    "type": "start",
                    "messageId": message_id,
                    "messageMetadata": {}
                }, ensure_ascii=False)
            }
            async for response_item in stream:
                print(response_item)
                response_item_ui_message = sk_agent_response_item_to_ui_message(response_item)
                for part in response_item_ui_message.parts:
                    yield {
                        "id": str(uuid.uuid4()),
                        "event": "message",
                        "data": json.dumps(part.model_dump(), ensure_ascii=False)
                    }
                    
            yield {
                "id": str(uuid.uuid4()),
                "event": "message",
                "data": json.dumps({
                    "type": "finish",
                    "messageMetadata": {}
                }, ensure_ascii=False)
            }                
        except Exception as e:
            logger.error(f"Error in chat stream: {str(e)}")
            async for error_message in error_event_generator(str(e)):
                yield error_message
            return

    return EventSourceResponse(event_generator(), headers={
        "x-vercel-ai-ui-message-stream": "v1",
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })
