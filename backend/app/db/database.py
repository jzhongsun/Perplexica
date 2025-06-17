from typing import Any, AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

from app.core.config import get_settings

settings = get_settings()

# Store engines and session factories per user
user_engines: Dict[str, AsyncEngine] = {}
user_session_factories: Dict[str, async_sessionmaker] = {}

def get_user_db_url(user_id: str) -> str:
    """Get database URL for a specific user."""
    # Create user database directory if it doesn't exist
    os.makedirs(f"./data/db/{user_id}", exist_ok=True)
    return f"sqlite+aiosqlite:///./data/db/{user_id}/user_db.db"

def get_user_engine(user_id: str):
    """Get or create engine for a specific user."""
    if user_id not in user_engines:
        db_url = get_user_db_url(user_id)
        user_engines[user_id] = create_async_engine(
            db_url,
            poolclass=NullPool,
            echo=settings.SQL_DEBUG
        )
    return user_engines[user_id]

def get_user_session_factory(user_id: str) -> async_sessionmaker:
    """Get or create session factory for a specific user."""
    if user_id not in user_session_factories:
        engine = get_user_engine(user_id)
        user_session_factories[user_id] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return user_session_factories[user_id]

async def get_user_session(user_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions for a specific user."""
    session_factory = get_user_session_factory(user_id)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close() 