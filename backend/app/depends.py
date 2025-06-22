from app.db.schemas import User
from app.db.service import UserDbService
from app.features.chat.service import ChatService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_app_session, get_user_session


async def get_current_user() -> User:
    return User(id="dev", email="dev@test.com", username="dev", full_name="Dev User")

async def get_app_database_service() -> UserDbService:
    session = await get_app_session()
    return UserDbService(session=session, user_id="app")


async def get_user_database_service(
    user: User = Depends(get_current_user),
) -> UserDbService:
    await UserDbService.ensure_user_db_initialized(user.id)
    session = await get_user_session(user.id)
    return UserDbService(session=session, user_id=user.id)


async def get_chat_service(
    user: User = Depends(get_current_user),
) -> ChatService:
    """Get chat service with proper session management."""
    return await ChatService.create(user)
