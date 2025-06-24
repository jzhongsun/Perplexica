import json
import os
import uuid
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import traceback

from app.db.models import DbMessage, DbMessagePart
from app.db.schemas import ChatCreate, User
from fastapi import HTTPException

from app.db.service import UserDbService
# from app.features.search import get_search_handler
from .schemas import (
    ChatRequest,
    NonStreamResponse,
    StreamResponse,
    MessageMetadata,
    ChatResponse,
    Message,
    ChatHistory,
    ChatMetadata,
    ChatFile,
    MessagesResponse,
)
import a2a.types as a2a_types
from a2a.client import A2AClient
import httpx
from app.core.utils.messages import ui_message_to_a2a_message
from app.core.ui_messages import (
    UIMessage,
    UIMessagePart,
    TextUIPart,
    FileUIPart,
    ReasoningUIPart,
    SourceUrlUIPart,
    SourceDocumentUIPart,
)

logger = logging.getLogger(__name__)

A2A_BASE_URL = os.getenv("A2A_BASE_URL", "http://localhost:10010")
A2A_BASE_AGENT_URL = os.getenv(
    "A2A_BASE_AGENT_URL", "http://localhost:10010/web_search/"
)

FOCUS_MODE_2_AGENT_URL = {
    "web_search": f"{A2A_BASE_AGENT_URL}/web_search/",
    "web_search_and_answer": f"{A2A_BASE_AGENT_URL}/web_search_and_answer/",
    "web_search_and_answer_with_files": f"{A2A_BASE_AGENT_URL}/web_search_and_answer_with_files/",
    "web_search_and_answer_with_files_and_context": f"{A2A_BASE_AGENT_URL}/web_search_and_answer_with_files_and_context/",
}


class ChatService:
    """Chat service class."""

    def __init__(self, user: User):
        """Initialize chat service."""
        self.user = user
        self.chats = {}

    async def __aenter__(self):
        self.db = await UserDbService.create(self.user.id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "db"):
            await self.db.__aexit__(exc_type, exc_val, exc_tb)

    @classmethod
    async def create(cls, user: User) -> "ChatService":
        """Create a new ChatService instance."""
        service = cls(user)
        return await service.__aenter__()

    async def resolve_agent_client(self, options: Dict[str, Any]) -> A2AClient:
        a2a_client = A2AClient(
            httpx_client=httpx.AsyncClient(),
            url=(
                FOCUS_MODE_2_AGENT_URL[options["focus_mode"]]
                if options
                and "focus_mode" in options
                and options["focus_mode"] in FOCUS_MODE_2_AGENT_URL
                else A2A_BASE_AGENT_URL
            ),
        )
        return a2a_client

    async def chat_stream(
        self, chat_id: str, messages: List[UIMessage], options: Dict[str, Any] = {}
    ) -> AsyncGenerator[a2a_types.SendStreamingMessageResponse, None]:

        chat = await self.db.fetch_chat(chat_id) if chat_id else None
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        """Chat stream."""
        agent_client = await self.resolve_agent_client(options)

        request_id = str(uuid.uuid4())
        user_message = ui_message_to_a2a_message(messages[-1], chat_id)
        stream = agent_client.send_message_streaming(
            request=a2a_types.SendStreamingMessageRequest(
                id=request_id,
                params=a2a_types.MessageSendParams(
                    message=user_message,
                    metadata={},
                ),
            )
        )
        task_id = None
        context_id = None
        agent_id = "entry_agent"

        response_messages = {}
        async for response in stream:
            yield response

            if isinstance(response.root.result, a2a_types.JSONRPCErrorResponse):
                logger.error(f"Error in chat stream: {response.root.result.error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error in chat stream: {response.root.result.error}",
                )

            success_response = response.root
            if isinstance(success_response.result, a2a_types.TaskArtifactUpdateEvent):
                await self.db.create_artifact(
                    success_response.result.artifact, task_id, context_id
                )
            elif isinstance(success_response.result, a2a_types.TaskStatusUpdateEvent):
                # logger.info(f"TaskStatusUpdateEvent: {success_response}")
                status = success_response.result.status
                if status.state == a2a_types.TaskState.submitted:
                    continue

                status_message = success_response.result.status.message
                if status_message is None:
                    continue

                if status_message.messageId not in response_messages.keys():
                    response_messages[status_message.messageId] = status_message

                # append the content of the status message to the previous message
                previous_message: a2a_types.Message = response_messages.get(
                    status_message.messageId
                )
                if previous_message is None or previous_message == status_message:
                    continue

                # logger.info(f"Appending status message to previous message: {previous_message} and {status_message}")
                previous_message.parts.extend(status_message.parts)

            elif isinstance(success_response.result, a2a_types.Task):
                task = response.root.result
                if task.status.state == a2a_types.TaskState.submitted:
                    task_id = task.id
                    context_id = task.contextId
                    await self.db.create_task(task, chat_id, agent_id)
                    await self.db.create_message(
                        user_message, chat_id, task_id, context_id
                    )
                    if user_message.parts and len(user_message.parts) > 0:
                        await self.db.create_message_parts(
                            user_message.messageId, user_message.parts
                        )
                elif task.status.state == a2a_types.TaskState.failed:
                    logger.error(f"Task failed: {task}")
                elif task.status.state == a2a_types.TaskState.completed:
                    logger.info(f"Task completed: {task}")
                elif task.status.state == a2a_types.TaskState.working:
                    logger.info(f"Task working: {task}")
                else:
                    logger.info(f"Task other status: {task}")

            elif isinstance(success_response.result, a2a_types.Message):
                logger.info(f"a2a - message: {success_response}")
                await self.db.create_message(
                    success_response, chat_id, task_id, context_id
                )
                if (
                    success_response.result.parts
                    and len(success_response.result.parts) > 0
                ):
                    await self.db.create_message_parts(
                        success_response.result.messageId, success_response.result.parts
                    )

        logger.info(f"Creating final messages: {response_messages.keys()}")
        for message_id, message in response_messages.items():
            await self.db.create_message(message, chat_id, task_id, context_id)
            if message.parts and len(message.parts) > 0:
                input_parts: List[a2a_types.Part] = message.parts
                final_parts: List[a2a_types.Part] = []
                final_text_part: a2a_types.Part = None
                for part in input_parts:
                    if isinstance(part.root, a2a_types.TextPart):
                        if final_text_part is None:
                            final_text_part = part
                            final_parts.append(final_text_part)
                        else:
                            final_text_part.root.text += part.root.text
                    else:
                        final_parts.append(part)
                await self.db.create_message_parts(message_id, final_parts)

    async def create_chat(self, request: ChatRequest) -> ChatHistory:
        """Create a new chat."""
        logger.info(
            f"Creating chat: chat_id='{request.chatId}' messages={request.messages} options={request.options}"
        )
        try:
            chat = await self.db.create_chat(
                ChatCreate(
                    id=request.chatId if request.chatId else str(uuid.uuid4()),
                    title=request.title if request.title else "New chat",
                    focus_mode=request.options.focusMode if request.options else "web_search",
                    optimization_mode=request.options.optimizationMode if request.options else "speed",
                    files=request.files if request.files else [],
                    userId=self.user.id,
                )
            )
            return await self.get_chat(chat.id)
        except Exception as e:
            error_msg = (
                f"Failed to create chat: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            )
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    async def list_chats(self) -> List[ChatMetadata]:
        """List all chats."""
        try:
            chats = await self.db.fetch_chats()
            return [
                ChatMetadata(
                    id=chat.id,
                    title=chat.title,
                    focusMode=chat.focus_mode,
                    createdAt=chat.created_at,
                    updatedAt=chat.updated_at,
                )
                for chat in chats
            ]
        except Exception as e:
            logger.error(f"Failed to list chats: {str(e)}, {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, detail=f"Failed to list chats: {str(e)}"
            )

    async def get_chat(self, chat_id: str) -> ChatHistory:
        """Get chat by ID."""
        try:
            chat = await self.db.fetch_chat(chat_id)
            if chat is None:
                raise HTTPException(status_code=404, detail="Chat not found")

            return ChatHistory(
                chat_id=chat.id,
                chat=ChatMetadata(
                    id=chat.id,
                    title=chat.title,
                    focusMode=chat.focus_mode,
                    # optimizationMode=chat.optimization_mode,
                    files=[
                        ChatFile(name=file.name, fileId=file.file_id)
                        for file in chat.files
                    ],
                    createdAt=chat.created_at,
                    updatedAt=chat.updated_at,
                ),
                messages=[],
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get chat: {str(e)}, {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to get chat: {str(e)}")

    async def delete_chat(self, chat_id: str) -> None:
        """Delete chat by ID."""
        try:
            await self.db.delete_chat(chat_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete chat: {str(e)}, {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete chat: {str(e)}"
            )

    async def _prepare_messages(self, request: ChatRequest) -> List[a2a_types.Message]:
        """Convert chat history to a2a messages."""
        messages: List[a2a_types.Message] = []
        for role, content in request.history:
            if role == "human":
                messages.append(
                    a2a_types.Message(content=content, role=a2a_types.Role.user)
                )
            elif role == "assistant":
                messages.append(
                    a2a_types.Message(content=content, role=a2a_types.Role.agent)
                )
        return messages

    async def _save_message(
        self,
        message_id: str,
        chat_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Save message to database with metadata."""
        metadata = MessageMetadata(createdAt=datetime.now(), sources=sources)

        await self.db_service.create_message(
            {
                "messageId": message_id,
                "chatId": chat_id,
                "role": role,
                "content": content,
                "metadata": metadata.model_dump_json(),
            }
        )

    async def _save_chat_history(self, request: ChatRequest, message_id: str) -> None:
        """Save chat and message history."""
        # Check if chat exists
        chat = await self.db_service.get_chat(request.message.chatId)

        if not chat:
            # Create new chat
            await self.db_service.create_chat(
                {
                    "id": request.message.chatId,
                    "title": request.message.content,
                    "focusMode": request.focusMode,
                    "files": [
                        await self.file_service.get_file_details(file_id)
                        for file_id in request.files
                    ],
                }
            )

        # Check if message exists
        existing_message = await self.db_service.get_message(message_id)

        if existing_message:
            # Delete all messages after this one
            await self.db_service.delete_messages_after(
                existing_message.id, request.message.chatId
            )
        else:
            # Save new message
            await self._save_message(
                message_id, request.message.chatId, "user", request.message.content
            )

    def build_ui_message_part(self, message_part: DbMessagePart) -> UIMessagePart:
        if message_part.part_type == "text":
            return TextUIPart(text=message_part.part_data["text"])
        else:
            logger.warning(f"Unknown part type: {message_part.part_type}")
            return None

    def build_ui_message(
        self, message: DbMessage, message_parts: List[DbMessagePart]
    ) -> UIMessage:
        parts = []
        for message_part in message_parts:
            part = self.build_ui_message_part(message_part)
            if part is not None:
                parts.append(part)
        return UIMessage(
            id=message.id,
            role="user" if message.role == "user" else "assistant",
            parts=parts,
            metadata=message.metadata,
        )

    async def fetch_messages_of_chat(
        self, chat_id: str, offset: int = 0, limit: int = 100
    ) -> MessagesResponse:
        """Fetch messages of chat by ID."""
        import app.db.converters as converters

        logger.info(
            f"Fetching messages of chat: {chat_id}, offset: {offset}, limit: {limit}"
        )
        try:
            messages = await self.db.fetch_messages(chat_id, offset=offset, limit=limit)
            message_ids = [message.id for message in messages]
            message_parts = await self.db.fetch_message_parts(message_ids)
            message_parts_dict = {}
            for part in message_parts:
                if part.message_id not in message_parts_dict:
                    message_parts_dict[part.message_id] = []
                message_parts_dict[part.message_id].append(part)
            ui_messages = []
            for message in messages:
                ui_messages.append(
                    converters.convert_db_message_to_ui_message(
                        message, message_parts_dict.get(message.id, [])
                    )
                )

            return MessagesResponse(
                chatId=chat_id,
                messages=ui_messages,
            )
        except Exception as e:
            logger.error(
                f"Error in fetch messages of chat: {str(e)}, {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Error in fetch messages of chat: {str(e)}"
            )
