from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class DbBase(DeclarativeBase):
    pass

class DbMessagePart(DbBase):
    __tablename__ = "message_parts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id"), nullable=False)
    part_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    part_type: Mapped[str] = mapped_column(SQLEnum("text", "file", "data", name="part_types"), nullable=False)
    part_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Relationship
    message: Mapped["DbMessage"] = relationship("Message", back_populates="parts")
    
class DbMessageArtifact(DbBase):
    __tablename__ = "message_artifacts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    message_id: Mapped[str] = mapped_column(String, ForeignKey("messages.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(SQLEnum("text", "file", "data", name="artifact_types"), nullable=False)
    artifact_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Relationship
    message: Mapped["DbMessage"] = relationship("Message", back_populates="artifacts")

class DbMessage(DbBase):
    """Message model for storing chat messages."""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum("assistant", "user", name="role_types"), nullable=False)
    parts: Mapped[List[DbMessagePart]] = relationship("MessagePart", back_populates="message", cascade="all, delete-orphan")
    artifacts: Mapped[List[DbMessageArtifact]] = relationship("MessageArtifact", back_populates="message", cascade="all, delete-orphan")
    
    # Relationship
    chat: Mapped["DbChat"] = relationship("Chat", back_populates="messages")

class DbChat(DbBase):
    """Chat model for storing chat sessions."""
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    focus_mode: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[List[dict]] = mapped_column(JSON, default=list)
    
    # Relationship
    messages: Mapped[List[DbMessage]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan") 