from datetime import datetime
from typing import List, Optional
from sqlalchemy import JSON, String, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Message(Base):
    """Message model for storing chat messages."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    chat_id: Mapped[str] = mapped_column(String, ForeignKey("chats.id"), nullable=False)
    message_id: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(SQLEnum("assistant", "user", name="role_types"), nullable=False)
    extra_info: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationship
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

class Chat(Base):
    """Chat model for storing chat sessions."""
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    focus_mode: Mapped[str] = mapped_column(String, nullable=False)
    files: Mapped[List[dict]] = mapped_column(JSON, default=list)
    
    # Relationship
    messages: Mapped[List[Message]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan") 