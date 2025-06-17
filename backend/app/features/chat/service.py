import json
import uuid
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime

from fastapi import HTTPException

from app.db.service import DatabaseService
from app.features.providers import get_chat_model, get_embedding_model
from app.features.files.service import FileService
from app.features.search import get_search_handler
from .schemas import (
    ChatRequest,
    NonStreamResponse,
    StreamResponse,
    MessageMetadata,
    ChatResponse,
    Message,
    ChatHistory,
    ChatMetadata
)
import a2a.types as a2a_types

class ChatService:
    """Chat service class."""
    
    def __init__(self):
        """Initialize chat service."""
        self.chats = {}  # In-memory storage
    
    async def create_chat(self, request: ChatRequest) -> ChatResponse:
        """Create a new chat."""
        print(request)
        try:
            chat_id = str(uuid.uuid4())
            
            # Create new chat
            message = Message(
                chat_id=chat_id,
                message_id=request.message.message_id,
                role="user",
                content=request.message.content,
                timestamp=datetime.now()
            )
            
            # Store chat
            self.chats[chat_id] = {
                'messages': [message],
                'metadata': ChatMetadata(
                    chat_id=chat_id,
                    title=f"Chat {len(self.chats) + 1}",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            }
            
            # Generate assistant response (mock)
            assistant_message = Message(
                chat_id=chat_id,
                message_id=request.message.message_id,
                role="assistant",
                content=f"Echo: {request.message}",  # Replace with actual AI response
                timestamp=datetime.now()
            )
            self.chats[chat_id]['messages'].append(assistant_message)
            
            return ChatResponse(
                chat_id=chat_id,
                message=assistant_message
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create chat: {str(e)}"
            )
    
    async def list_chats(self) -> List[ChatMetadata]:
        """List all chats."""
        try:
            return [chat['metadata'] for chat in self.chats.values()]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list chats: {str(e)}"
            )
    
    async def get_chat(self, chat_id: str) -> ChatHistory:
        """Get chat by ID."""
        try:
            if chat_id not in self.chats:
                raise HTTPException(
                    status_code=404,
                    detail="Chat not found"
                )
            
            chat = self.chats[chat_id]
            return ChatHistory(
                chat_id=chat_id,
                messages=chat['messages'],
                metadata=chat['metadata']
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get chat: {str(e)}"
            )
    
    async def delete_chat(self, chat_id: str) -> None:
        """Delete chat by ID."""
        try:
            if chat_id not in self.chats:
                raise HTTPException(
                    status_code=404,
                    detail="Chat not found"
                )
            
            del self.chats[chat_id]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete chat: {str(e)}"
            )

    async def _prepare_messages(
        self,
        request: ChatRequest
    ) -> List[a2a_types.Message]:
        """Convert chat history to LangChain messages."""
        messages: List[a2a_types.Message] = []
        for role, content in request.history:
            if role == "human":
                messages.append(a2a_types.Message(content=content, role=a2a_types.Role.user))
            elif role == "assistant":
                messages.append(a2a_types.Message(content=content, role=a2a_types.Role.agent))
        return messages
    async def _save_message(
        self,
        message_id: str,
        chat_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Save message to database with metadata."""
        metadata = MessageMetadata(
            createdAt=datetime.now(),
            sources=sources
        )
        
        await self.db_service.create_message({
            "messageId": message_id,
            "chatId": chat_id,
            "role": role,
            "content": content,
            "metadata": metadata.model_dump_json()
        })

    async def _save_chat_history(
        self,
        request: ChatRequest,
        message_id: str
    ) -> None:
        """Save chat and message history."""
        # Check if chat exists
        chat = await self.db_service.get_chat(request.message.chatId)
        
        if not chat:
            # Create new chat
            await self.db_service.create_chat({
                "id": request.message.chatId,
                "title": request.message.content,
                "focusMode": request.focusMode,
                "files": [
                    await self.file_service.get_file_details(file_id)
                    for file_id in request.files
                ]
            })
        
        # Check if message exists
        existing_message = await self.db_service.get_message(message_id)
        
        if existing_message:
            # Delete all messages after this one
            await self.db_service.delete_messages_after(
                existing_message.id,
                request.message.chatId
            )
        else:
            # Save new message
            await self._save_message(
                message_id,
                request.message.chatId,
                "user",
                request.message.content
            )

    async def stream_response(
        self,
        request: ChatRequest
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response for chat request."""
        try:
            # Generate message IDs
            human_message_id = request.message.messageId or str(uuid.uuid4())
            ai_message_id = str(uuid.uuid4())

            # Save chat history
            await self._save_chat_history(request, human_message_id)

            # Prepare models and context
            messages = await self._prepare_messages(request)

            # Get search handler
            search_handler = get_search_handler(request.focusMode)
            if not search_handler:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid focus mode"
                )

            # Set up streaming
            # callback = AsyncIteratorCallbackHandler()
            # chat_model.callbacks = [callback]

            # Start search and answer process
            response_content = ""
            sources = []

            # Start model call in background
            search_task = asyncio.create_task(
                search_handler.search_and_answer(
                    request.message.content,
                    messages,
                    request.chatModel,
                    request.embeddingModel,
                    request.optimizationMode,
                    request.files,
                    request.systemInstructions
                )
            )

            try:
                async for token in result.aiter():
                    response_content += token
                    yield json.dumps(
                        StreamResponse(
                            type="message",
                            data=token,
                            messageId=ai_message_id
                        ).model_dump()
                    ) + "\n"

                # Get sources from response if any
                # if hasattr(result, "additional_kwargs"):
                #     sources = result.additional_kwargs.get("sources", [])
                #     if sources:
                #         yield json.dumps(
                #             StreamResponse(
                #                 type="sources",
                #                 sources=sources,
                #                 messageId=ai_message_id
                #             ).model_dump()
                #         ) + "\n"

                # Save assistant message
                await self._save_message(
                    ai_message_id,
                    request.message.chatId,
                    "assistant",
                    response_content,
                    sources
                )

                # Send end marker
                yield json.dumps(
                    StreamResponse(
                        type="messageEnd",
                        messageId=ai_message_id
                    ).model_dump()
                ) + "\n"

            except Exception as e:
                yield json.dumps(
                    StreamResponse(
                        type="error",
                        data=str(e),
                        messageId=ai_message_id
                    ).model_dump()
                ) + "\n"
                raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in chat stream: {str(e)}"
            )

    async def get_response(self, request: ChatRequest) -> NonStreamResponse:
        """Generate complete response for chat request."""
        try:
            # Generate message IDs
            human_message_id = request.message.messageId or str(uuid.uuid4())
            ai_message_id = str(uuid.uuid4())

            # Save chat history
            await self._save_chat_history(request, human_message_id)

            # Prepare models and context
            messages = await self._prepare_messages(request)
            chat_model, embedding_model = await self._get_models(request)

            # Get search handler
            search_handler = get_search_handler(request.focusMode)
            if not search_handler:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid focus mode"
                )

            # Generate response
            result = await search_handler.search_and_answer(
                request.message.content,
                messages,
                chat_model,
                embedding_model,
                request.optimizationMode,
                request.files,
                request.systemInstructions
            )
            
            # Extract sources if any
            sources = []
            if hasattr(result, "additional_kwargs"):
                sources = result.additional_kwargs.get("sources", [])

            # Save assistant message
            await self._save_message(
                ai_message_id,
                request.message.chatId,
                "assistant",
                result.text,
                sources
            )

            return NonStreamResponse(
                message=result.text,
                sources=sources
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in chat: {str(e)}"
            ) 