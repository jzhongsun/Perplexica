from app.db.models import DbAppBase, DbUserBase
from app.db.database import get_app_engine, get_user_engine

async def init_app_db():
    """Initialize the application database."""
    engine = get_app_engine()
    async with engine.begin() as conn:
        await conn.run_sync(DbAppBase.metadata.create_all)

async def init_user_db(user_id: str):
    """Initialize a user-specific database."""
    engine = get_user_engine(user_id)
    async with engine.begin() as conn:
        await conn.run_sync(DbUserBase.metadata.create_all)

async def init_db():
    """Initialize all databases."""
    await init_app_db() 