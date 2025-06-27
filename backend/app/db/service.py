from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import DbChat, DbMessage, DbTask, DbUserBase, DbMessagePart, DbArtifactPart, DbArtifact
from .schemas import ChatCreate, MessageCreate
from .database import get_user_engine, get_user_session
from app.core.ui_messages import UIMessage, UIMessagePart
import a2a.types as a2a_types
from loguru import logger

class UserDbService:
    """Service for database operations."""

    def __init__(self, session: AsyncSession, user_id: str, manage_session: bool = False):
        self.session = session
        self.user_id = user_id
        self.manage_session = manage_session  # Whether this service should manage the session lifecycle

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Only manage session if explicitly told to do so
        if self.manage_session:
            if exc_type is not None:
                await self.session.rollback()
            await self.session.close()

    @classmethod
    async def create(cls, user_id: str) -> "UserDbService":
        """Create a new UserDbService instance with a managed session."""
        async with get_user_session(user_id) as session:
            return cls(session, user_id, manage_session=False)  # Session is managed by context manager

    @classmethod
    async def ensure_user_db_initialized(cls, user_id: str):
        """Initialize database for a new user."""
        engine = get_user_engine(user_id)
        async with engine.begin() as conn:
            await conn.run_sync(DbUserBase.metadata.create_all)

    async def create_chat(self, chat_data: ChatCreate) -> DbChat:
        """Create a new chat."""
        chat = DbChat(
            id=chat_data.id,
            title=chat_data.title,
            focus_mode=chat_data.focus_mode,
            files=[file.model_dump() for file in chat_data.files],
            user_id=self.user_id,  # Add user_id to chat
        )
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def fetch_chat(self, chat_id: str) -> Optional[DbChat]:
        """Get a chat by ID."""
        query = (
            select(DbChat)
            .where(DbChat.id == chat_id, DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_chats(self) -> List[DbChat]:
        """List all chats for the current user."""
        query = (
            select(DbChat)
            .where(DbChat.user_id == self.user_id)
            .order_by(DbChat.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        delete_message_parts_query = (
            delete(DbMessagePart)
            .where(DbMessagePart.message_id.in_(select(DbMessage.id).where(DbMessage.chat_id == chat_id)))
        )
        delete_artifact_parts_query = (
            delete(DbArtifactPart)
            .where(DbArtifactPart.artifact_id.in_(select(DbArtifact.id).where(DbArtifact.task_id.in_(select(DbTask.id).where(DbTask.chat_id == chat_id)))))
        )
        delete_artifacts_query = (
            delete(DbArtifact)
            .where(DbArtifact.task_id.in_(select(DbTask.id).where(DbTask.chat_id == chat_id)))
        )
        delete_messages_query = (
            delete(DbMessage)
            .where(DbMessage.chat_id == chat_id)
        )
        delete_tasks_query = (
            delete(DbTask)
            .where(DbTask.chat_id == chat_id)
        )
        
        delete_chat_query = (
            delete(DbChat)
            .where(DbChat.id == chat_id, DbChat.user_id == self.user_id)
        )
        result = await self.session.execute(delete_message_parts_query)
        result = await self.session.execute(delete_artifact_parts_query)
        result = await self.session.execute(delete_artifacts_query)
        result = await self.session.execute(delete_messages_query)
        result = await self.session.execute(delete_tasks_query)
        result = await self.session.execute(delete_chat_query)
        await self.session.commit()
        return result.rowcount > 0

    async def create_message_x(self, message_data: MessageCreate) -> DbMessage:
        """Create a new message."""
        # Verify the chat belongs to the current user
        chat = await self.fetch_chat(message_data.chat_id)
        if not chat or chat.user_id != self.user_id:
            raise ValueError("Chat not found or access denied")

        message = DbMessage(
            content=message_data.content,
            chat_id=message_data.chat_id,
            message_id=message_data.message_id,
            role=message_data.role,
            extra_info=message_data.extra_info,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_chat_messages(self, chat_id: str) -> List[DbMessage]:
        """Get all messages for a chat."""
        # Verify the chat belongs to the current user
        chat = await self.fetch_chat(chat_id)
        if not chat or chat.user_id != self.user_id:
            return []

        query = select(DbMessage).where(DbMessage.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    def __build_message_content(self, message: UIMessage) -> str:
        content = ""
        for part in message.parts:
            if part.type == "text":
                content += part.text
        return content
    
    async def create_message(self, message: UIMessage, chat_id: str, task_id: str, context_id: str | None = None) -> DbMessage:
        message = DbMessage(
            id=message.id,
            content=self.__build_message_content(message),
            chat_id=chat_id,
            role=message.role,
            task_id=task_id,
            context_id=context_id,
            _metadata=message.metadata,
            extensions=[],
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        logger.info(f"Created message: {message}")
        return message
        
    async def fetch_message(self, message_id: str) -> Optional[DbMessage]:
        query = select(DbMessage).where(DbMessage.id == message_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def fetch_messages(self, chat_id: str, offset: int = 0, limit: int = 5) -> List[DbMessage]:
        query = select(DbMessage).where(DbMessage.chat_id == chat_id).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_artifact(self, artifact: a2a_types.Artifact, task_id: str, context_id: str | None = None) -> DbArtifact:
        artifact = DbArtifact(
            id=artifact.artifactId,
            name=artifact.name,
            description=artifact.description,
            _metadata=artifact.metadata,
            extensions=artifact.extensions,
            task_id=task_id,
            context_id=context_id
        )
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        logger.info(f"Created artifact: {artifact}")
        return artifact
    
    async def fetch_artifact(self, artifact_id: str) -> Optional[DbArtifact]:
        query = select(DbArtifact).where(DbArtifact.id == artifact_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def fetch_artifacts(self, task_id: str) -> List[DbArtifact]:
        query = select(DbArtifact).where(DbArtifact.task_id == task_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_message_parts(self, message_id: str, parts: List[UIMessagePart]) -> List[DbMessagePart]:
        message_parts = [DbMessagePart(
            id=str(uuid.uuid4()),
            message_id=message_id,
            part_type=part.type,
            part_data=part.model_dump(exclude_none=True),
            _metadata={
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
            part_index=index,
        ) for index, part in enumerate(parts)]
        self.session.add_all(message_parts)
        await self.session.commit()
        logger.info(f"Created message parts: {message_parts}")
        return message_parts
    
    async def fetch_message_parts(self, message_ids: List[str]) -> List[DbMessagePart]:
        query = select(DbMessagePart).where(DbMessagePart.message_id.in_(message_ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())    
    
    async def create_artifact_parts(self, artifact_id: str, parts: List[a2a_types.Part]) -> List[DbArtifactPart]:
        artifact_parts = [DbArtifactPart(
            id=str(uuid.uuid4()),
            artifact_id=artifact_id,
            part_type=part.type,
            part_data=part.model_dump(exclude_none=True) if part.type == "text" else {},
            _metadata={
                "createdAt": datetime.now(timezone.utc).isoformat(),
            },
            part_index=index,
        ) for index, part in enumerate(parts)]
        self.session.add_all(artifact_parts)
        await self.session.commit()
        logger.info(f"Created artifact parts: {artifact_parts}")
        return artifact_parts

    async def fetch_artifact_parts(self, artifact_id: str) -> List[DbArtifactPart]:
        query = select(DbArtifactPart).where(DbArtifactPart.artifact_id == artifact_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())    
    
    
    async def create_task(self, task: a2a_types.Task, chat_id: str, agent_id: str) -> DbTask:
        task = DbTask(
            id=task.id,
            chat_id=chat_id,
            task_id=task.id,
            context_id=task.contextId,
            agent_id=agent_id,
            status=task.status.state.value,
            _metadata=task.metadata,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        logger.info(f"Created task: {task}")
        return task
    
    async def fetch_task(self, task_id: str) -> Optional[DbTask]:
        query = select(DbTask).where(DbTask.id == task_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def fetch_tasks(self, chat_id: str) -> List[DbTask]:
        query = select(DbTask).where(DbTask.chat_id == chat_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

