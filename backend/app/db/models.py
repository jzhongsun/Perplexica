from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import JSON, String, Integer, ForeignKey, Enum as SQLEnum, Column, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DbUserBase(DeclarativeBase):
    pass

class DbMessagePart(DbUserBase):
    __tablename__ = "message_parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id"), nullable=False)
    part_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    part_type: Mapped[str] = mapped_column(SQLEnum("text", "file", "data", name="part_types"), nullable=False)
    part_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    _metadata: Mapped[dict] = mapped_column(JSON, name="metadata", nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 

    # Relationship
    # message: Mapped["DbMessage"] = relationship("Message", back_populates="parts")

class DbArtifactPart(DbUserBase):
    __tablename__ = "artifact_parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(String, ForeignKey("artifacts.id"), nullable=False)
    part_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    part_type: Mapped[str] = mapped_column(SQLEnum("text", "file", "data", name="part_types"), nullable=False)
    part_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    _metadata: Mapped[dict] = mapped_column(JSON, name="metadata", nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 

    # Relationship
    # artifact: Mapped["DbArtifact"] = relationship("Artifact", back_populates="parts")


    
class DbArtifact(DbUserBase):
    __tablename__ = "artifacts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    context_id: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    _metadata: Mapped[dict] = mapped_column(JSON, name="metadata", nullable=True)
    extensions: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 
    
    # Relationship
    # message: Mapped["DbMessage"] = relationship("Message", back_populates="artifacts")

class DbMessage(DbUserBase):
    """Message model for storing chat messages."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, ForeignKey("tasks.id"), nullable=True)
    context_id: Mapped[str] = mapped_column(String, nullable=True)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum("assistant", "user", name="role_types"), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    _metadata: Mapped[dict] = mapped_column(JSON, name="metadata", nullable=True)
    extensions: Mapped[List[str]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 
    
    # parts: Mapped[List[DbMessagePart]] = relationship("MessagePart", back_populates="message", cascade="all, delete-orphan")
    # artifacts: Mapped[List[DbMessageArtifact]] = relationship("MessageArtifact", back_populates="message", cascade="all, delete-orphan")
    
    # Relationship
    # chat: Mapped["DbChat"] = relationship("Chat", back_populates="messages")

class DbTask(DbUserBase):
    __tablename__ = "tasks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    context_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(SQLEnum("submitted", "running", "completed", "failed", name="task_statuses"), nullable=False)
    _metadata: Mapped[dict] = mapped_column(JSON, name="metadata", nullable=True)
    extensions: Mapped[List[str]] = mapped_column(JSON, nullable=True)

    payload: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 

class DbChat(DbUserBase):
    """Chat model for storing chat sessions."""
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 
    
    focus_mode: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[List[dict]] = mapped_column(JSON, default=list)
    
    # Relationship
    # messages: Mapped[List[DbMessage]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")



class DbAppBase(DeclarativeBase):
    pass

class DbUser(DbAppBase):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    google_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    anonymous_token: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 