from typing import Any, AsyncGenerator, Dict
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

from app.core.config import get_settings

settings = get_settings()

# Store engines and session factories
user_engines: Dict[str, AsyncEngine] = {}
user_session_factories: Dict[str, async_sessionmaker] = {}
app_engine: AsyncEngine = None
app_session_factory: async_sessionmaker = None

def get_user_db_url(user_id: str) -> str:
    """Get database URL for a specific user."""
    # Create user database directory if it doesn't exist
    os.makedirs(f"./data/db_user/{user_id}", exist_ok=True)
    return f"sqlite+aiosqlite:///./data/db_user/{user_id}/user_db.db"

def get_app_db_url() -> str:
    """Get database URL for application data."""
    # Create app database directory if it doesn't exist
    os.makedirs("./data/db_app", exist_ok=True)
    return "sqlite+aiosqlite:///./data/db_app/app_db.db"

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

def get_app_engine():
    """Get or create engine for application data."""
    global app_engine
    if app_engine is None:
        db_url = get_app_db_url()
        app_engine = create_async_engine(
            db_url,
            poolclass=NullPool,
            echo=settings.SQL_DEBUG
        )
    return app_engine

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

def get_app_session_factory() -> async_sessionmaker:
    """Get or create session factory for application data."""
    global app_session_factory
    if app_session_factory is None:
        engine = get_app_engine()
        app_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return app_session_factory

async def get_user_session(user_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions for a specific user."""
    session_factory = get_user_session_factory(user_id)
    return session_factory()

async def get_app_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions for application data."""
    session_factory = get_app_session_factory()
    return session_factory()