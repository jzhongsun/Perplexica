import os
import uuid
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional, AsyncIterator
from datetime import datetime, timezone
import logging
import traceback

from novas_app.core.ui_message_stream import (
    ErrorUIMessageStreamPart,
    FinishUIMessageStreamPart,
    StartUIMessageStreamPart,
    TextDeltaUIMessageStreamPart,
    TextEndUIMessageStreamPart,
    TextStartUIMessageStreamPart,
    ToolInputAvailableUIMessageStreamPart,
    ToolOutputAvailableUIMessageStreamPart,
    UIMessageStreamPart,
)
from novas_app.db.models import DbMessage, DbMessagePart
from novas_app.db.schemas import ChatCreate, User
from fastapi import HTTPException
from pydantic import BaseModel

from novas_app.db.service import UserDbService

# from app.features.search import get_search_handler
from .schemas import (
    ChatRequest,
    MessageMetadata,
    ChatHistory,
    ChatMetadata,
    ChatFile,
    MessagesResponse,
)
import a2a.types as a2a_types
from a2a.client import Client, A2ACardResolver, ClientFactory, ClientConfig
import httpx
from novas_app.core.ui_messages import (
    ToolUIPartInputAvailable,
    ToolUIPartOutputAvailable,
    UIMessage,
    UIMessagePart,
    TextUIPart,
)

logger = logging.getLogger(__name__)

A2A_BASE_URL = os.getenv("A2A_BASE_URL", "http://localhost:10010")
A2A_BASE_AGENT_URL = os.getenv(
    "A2A_BASE_AGENT_URL", A2A_BASE_URL
)

FOCUS_MODE_2_AGENT_URL = {
    "stock_symbol_research": "/stock_symbol_research",
    "web_search": "/web_search",
}

CONTEXTUAL_QUERY_PROMPT_TEMPLATE = """
## Conversation context information is below.

<conversation_context>
{context}
</conversation_context>

Given the context information and the current query, provide a relevant response. The conversation history is provided for reference to maintain context and coherence.

## Follow these rules:

1. Use the conversation context only when it's relevant to the current query.
2. If the query is unrelated to the conversation history, focus solely on answering the query.
3. Avoid unnecessary references like "Based on the context..." or "The provided information...".

## Query: 
<query>
{query}
</query>

Answer:
"""

EMPTY_QUERY_PROMPT_TEMPLATE = """
Query: 
<query>
{query}
</query>

Answer:
"""

HTTPX_TIMEOUT = httpx.Timeout(
    connect=10.0,      # Connection timeout
    read=600.0,        # Read timeout (10 minutes for long AI responses)
    write=10.0,        # Write timeout
    pool=10.0          # Pool timeout
)

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

    async def resolve_agent_client(self, options: Dict[str, Any]) -> Client:
        logger.info(f"resolve_agent_client - options: {options}, FOCUS_MODE_2_AGENT_URL: {FOCUS_MODE_2_AGENT_URL}")
        a2a_url = FOCUS_MODE_2_AGENT_URL[options["focusMode"]] if options and "focusMode" in options and options["focusMode"] in FOCUS_MODE_2_AGENT_URL else A2A_BASE_AGENT_URL
        logger.info(f"resolved: A2A: options: {options} URL: {a2a_url}")
        
        # Configure httpx client with appropriate timeouts and connection handling
        httpx_client = httpx.AsyncClient(
            timeout=HTTPX_TIMEOUT,
            # Add connection pool limits to prevent resource exhaustion
            limits=httpx.Limits(
                max_keepalive_connections=50,
                max_connections=500,
                keepalive_expiry=30.0,
            ),
            # Follow redirects and retry on connection errors
            follow_redirects=True,
        )
        
        a2a_client = Client(
            httpx_client=httpx_client,
            url=a2a_url,
        )
        return a2a_client

    async def build_message_with_history(
        self,
        chat_id: str,
        user_message: UIMessage,
        task_id: str | None = None,
        context_id: str | None = None,
    ) -> a2a_types.Message:
        messages_response = await self.fetch_messages_of_chat(
            chat_id=chat_id, offset=0, limit=4
        )
        if messages_response is None:
            return user_message

        context = ""
        for message in messages_response.messages:
            if message.role == "user":
                context += f"\n<user>\n{message.content()}\n</user>\n"
            elif message.role == "assistant":
                context += f"\n<assistant>\n{message.content()}\n</assistant>\n"

        user_message_content = ""
        for part in user_message.parts:
            if part.type == "text":
                user_message_content += part.text

        if len(context) == 0:
            return a2a_types.Message(
                messageId=user_message.id,
                parts=[a2a_types.TextPart(text=user_message.content())],
                role=a2a_types.Role.user,
            )
        else:
            return a2a_types.Message(
                messageId=user_message.id,
                parts=[
                    a2a_types.TextPart(
                        text=CONTEXTUAL_QUERY_PROMPT_TEMPLATE.format(
                            context=context, query=user_message_content
                        )
                    )
                ],
                role=a2a_types.Role.user,
                metadata=user_message.metadata,
                taskId=task_id,
                contextId=context_id,
                extensions=[],
            )
    
    async def chat_stream(
        self,
        chat_id: str,
        messages: List[UIMessage],
        options: Dict[str, Any] = {}
    ) -> AsyncIterator[UIMessageStreamPart]:
        chat = await self.db.fetch_chat(chat_id) if chat_id else None
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        """Chat stream."""
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as httpx_client:
            relative_agent_url = FOCUS_MODE_2_AGENT_URL[options["focusMode"]] if options and "focusMode" in options and options["focusMode"] in FOCUS_MODE_2_AGENT_URL else A2A_BASE_AGENT_URL
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=A2A_BASE_URL + relative_agent_url,
            )
            agent_card = await resolver.get_agent_card()
            logger.info(f"agent_card: {agent_card}")
            
            client_factory = ClientFactory(
                config=ClientConfig(
                    streaming=True,
                    httpx_client=httpx_client,
                )
            )
            
            agent_client = client_factory.create(agent_card)
            async for part in self._chat_stream_internal(chat_id, agent_client, messages, options):
                if part is not None:
                    yield part

    async def _chat_stream_internal(
        self, chat_id: str, agent_client: Client, messages: List[UIMessage], options: Dict[str, Any] = {}
    ) -> AsyncIterator[UIMessageStreamPart]:

        request_id = str(uuid.uuid4())
        final_user_message_ui: UIMessage = messages[-1]
        final_user_message_a2a = await self.build_message_with_history(
            chat_id, final_user_message_ui
        )

        task_id = None
        context_id = None
        agent_id = "entry_agent"

        message_id = str(uuid.uuid4())

        response_message_parts_ref: Dict[str, UIMessagePart] = {}
        final_response_message_ui: UIMessage = UIMessage(
            id=message_id,
            role="assistant",
            parts=[],
            metadata={
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
        )
        yield StartUIMessageStreamPart(
            messageId=message_id, messageMetadata=final_response_message_ui.metadata
        )
        try:

            class ActiveMessageProps(BaseModel):
                reference_message_id: Optional[str] = None
                text_part_id: Optional[str] = None
                reasoning_part_id: Optional[str] = None

            active_message_props = ActiveMessageProps()

            stream = agent_client.send_message(
                request=final_user_message_a2a,
                # request=a2a_types.SendMessageRequest(
                #     id=request_id,
                #     params=a2a_types.MessageSendParams(
                #         message=final_user_message_a2a,
                #         metadata={},
                #     ),
                # )
            )
            
            a2a_task = None
            async for chunk in stream:
                task = None
                event = None
                message = None

                if isinstance(chunk, a2a_types.Message):
                    message = chunk
                elif isinstance(chunk, tuple):
                    task, event = chunk
                    
                print(f'{__file__} > {type(task)} {type(event)} {type(message)}')
                # yield None

                if isinstance(
                    event, a2a_types.TaskArtifactUpdateEvent
                ):
                    await self.db.create_artifact(
                        event.artifact, task_id, context_id
                    )
                elif isinstance(
                    event, a2a_types.TaskStatusUpdateEvent
                ):
                    # logger.info(f"TaskStatusUpdateEvent: {success_response}")
                    status = event.status
                    if status.state == a2a_types.TaskState.submitted:
                        continue

                    status_message = event.status.message
                    if status_message is None:
                        continue

                    if (
                        active_message_props.reference_message_id
                        != status_message.message_id
                    ):
                        if active_message_props.text_part_id is not None:
                            yield TextEndUIMessageStreamPart(
                                id=active_message_props.text_part_id
                            )
                            active_message_props.text_part_id = None
                        active_message_props.reference_message_id = (
                            status_message.message_id
                        )

                    for part in status_message.parts:
                        if isinstance(part.root, a2a_types.TextPart):
                            if active_message_props.text_part_id is None:
                                active_message_props.text_part_id = str(uuid.uuid4())
                                yield TextStartUIMessageStreamPart(
                                    id=active_message_props.text_part_id
                                )
                            yield TextDeltaUIMessageStreamPart(
                                id=active_message_props.text_part_id,
                                delta=part.root.text,
                            )
                            if (
                                response_message_parts_ref.get(status_message.message_id)
                                is None
                            ):
                                response_message_parts_ref[status_message.message_id] = (
                                    TextUIPart(text=part.root.text)
                                )
                                final_response_message_ui.parts.append(
                                    response_message_parts_ref[status_message.message_id]
                                )
                            else:
                                response_message_parts_ref[
                                    status_message.message_id
                                ].text += part.root.text
                        elif isinstance(part.root, a2a_types.DataPart):
                            # logger.info(f"Data part: {part.root}")
                            if part.root.metadata.get("inner_part_type") == "tool_call":
                                tool_call_data = part.root.data
                                tool_call_id = tool_call_data.get("tool_call_id")
                                if tool_call_id is None:
                                    tool_call_id = tool_call_data.get("id")
                                tool_name = tool_call_data.get("tool_name")
                                arguments = tool_call_data.get("arguments")
                                yield ToolInputAvailableUIMessageStreamPart(
                                    toolCallId=tool_call_id,
                                    toolName=tool_name,
                                    input=arguments,
                                )

                                response_message_parts_ref[tool_call_id] = (
                                    ToolUIPartInputAvailable(
                                        type=f"tool-{tool_name}",
                                        toolCallId=tool_call_id,
                                        input=arguments,
                                    )
                                )
                                final_response_message_ui.parts.append(
                                    response_message_parts_ref[tool_call_id]
                                )

                            elif (
                                part.root.metadata.get("inner_part_type")
                                == "tool_result"
                            ):
                                tool_result_data = part.root.data
                                tool_call_id = tool_result_data.get("tool_call_id")
                                if tool_call_id is None:
                                    tool_call_id = tool_result_data.get("id")
                                tool_name = tool_result_data.get("tool_name")
                                result = tool_result_data.get("result")
                                yield ToolOutputAvailableUIMessageStreamPart(
                                    toolCallId=tool_call_id,
                                    toolName=tool_name,
                                    output=result,
                                )
                                
                                previous_tool_call_message_part = response_message_parts_ref.get(tool_call_id)
                                response_message_parts_ref[tool_call_id] = (
                                    ToolUIPartOutputAvailable(
                                        type=f"tool-{tool_name}",
                                        toolCallId=tool_call_id,
                                        input=previous_tool_call_message_part.input if previous_tool_call_message_part else {},
                                        output=result,
                                        metadata={
                                            "inner_part_type": "tool_result",
                                            **part.root.metadata,
                                        },
                                    )
                                )
                                if previous_tool_call_message_part is None:
                                    final_response_message_ui.parts.append(
                                        response_message_parts_ref[tool_call_id]
                                    )
                                else:
                                    try:
                                        idx = final_response_message_ui.parts.index(previous_tool_call_message_part)
                                        final_response_message_ui.parts[idx] = response_message_parts_ref[tool_call_id]
                                    except ValueError:
                                        final_response_message_ui.parts.append(
                                            response_message_parts_ref[tool_call_id]
                                        )

                        elif isinstance(part.root, a2a_types.FilePart):
                            logger.info(f"File part: {part.root}")
                        else:
                            logger.info(f"Unknown part: {part.root}")

                if task is not None:
                    if task.status.state == a2a_types.TaskState.submitted:
                        task_id = task.id
                        context_id = task.context_id
                        if a2a_task is None:
                            a2a_task = task
                            await self.db.create_task(a2a_task, chat_id, agent_id)
                            await self.db.create_message(
                                final_user_message_ui, chat_id, task_id, context_id
                            )
                            if (
                                final_user_message_ui.parts
                                and len(final_user_message_ui.parts) > 0
                            ):
                                await self.db.create_message_parts(
                                    final_user_message_ui.id, final_user_message_ui.parts
                                )
                    elif task.status.state == a2a_types.TaskState.failed:
                        logger.error(f"Task failed: {task}")
                    elif task.status.state == a2a_types.TaskState.completed:
                        logger.info(f"Task completed: {task}")
                    elif task.status.state == a2a_types.TaskState.working:
                        # logger.info(f"Task working: {task}")
                        pass
                    else:
                        logger.info(f"Task other status: {task}")

                if message is not None:
                    # logger.info(f"a2a - message: {message}")
                    await self.db.create_message(
                        message, chat_id, task_id, context_id
                    )
                    if (
                        message.parts
                        and len(message.parts) > 0
                    ):
                        await self.db.create_message_parts(
                            message.message_id,
                            message.parts,
                        )

            if active_message_props.text_part_id is not None:
                yield TextEndUIMessageStreamPart(id=active_message_props.text_part_id)

            logger.info(
                f"Creating final message parts: {response_message_parts_ref.keys()}"
            )
            completed_at = datetime.now(timezone.utc).isoformat()
            final_response_message_ui.metadata["completedAt"] = completed_at
            await self.db.create_message(
                final_response_message_ui, chat_id, task_id, context_id
            )
            await self.db.create_message_parts(
                final_response_message_ui.id, final_response_message_ui.parts
            )
            yield FinishUIMessageStreamPart(
                messageId=message_id,
                messageMetadata={
                    "completedAt": completed_at,
                },
            )

        except asyncio.CancelledError:
            # Client disconnected or stream was cancelled - this is normal behavior
            logger.info(f"Chat stream cancelled for chat {chat_id} (client disconnected or stream cancelled)")
            # Re-raise to properly propagate the cancellation
            raise
        except Exception as e:
            error_msg = (
                f"Error in chat stream: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            )
            logger.error(error_msg)
            yield ErrorUIMessageStreamPart(errorText=str(e))

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
                    focus_mode=(
                        request.options.focusMode if request.options else "web_search"
                    ),
                    optimization_mode=(
                        request.options.optimizationMode if request.options else "speed"
                    ),
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
        for message in request.messages:
            role = message.role
            content = message.content
            if role == "user":
                messages.append(
                    a2a_types.Message(content=content, role=a2a_types.Role.user)
                )
            elif role == "assistant" or role == "agent":
                messages.append(
                    a2a_types.Message(content=content, role=a2a_types.Role.agent)
                )
            else:
                logger.warning(f"Unknown role: {role}")
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
        import novas_app.db.converters as converters

        logger.info(
            f"Fetching messages of chat: {chat_id}, offset: {offset}, limit: {limit}"
        )
        try:
            messages = await self.db.fetch_messages(chat_id, offset=offset, limit=limit)
            message_ids = [message.id for message in messages]
            message_parts = await self.db.fetch_message_parts(message_ids)
            message_parts_dict: Dict[str, List[DbMessagePart]] = {}
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
