from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from novas_app.db.models import DbUser
from novas_app.db.schemas import UserCreate
from novas_app.core.security import verify_password, get_password_hash

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[DbUser]:
        result = await self.db.execute(select(DbUser).where(DbUser.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_anonymous_token(self, token: str) -> Optional[DbUser]:
        result = await self.db.execute(select(DbUser).where(DbUser.anonymous_token == token))
        return result.scalar_one_or_none()

    async def authenticate_user(self, email: str, password: str) -> Optional[DbUser]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password:  # Google user or anonymous user
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def create_user(self, user_data: UserCreate) -> DbUser:
        # Check if user already exists
        if user_data.email:
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password) if user_data.password else None
        db_user = DbUser(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user

    async def create_google_user(self, user_data: UserCreate, google_id: str) -> DbUser:
        # Create new user with Google ID
        db_user = DbUser(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            google_id=google_id,
            hashed_password=None  # No password for Google users
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user

    async def create_anonymous_user(self, user_data: Optional[UserCreate] = None) -> DbUser:
        # Generate unique username and token
        anonymous_token = str(uuid.uuid4())
        username = user_data.username if user_data and user_data.username else f"anonymous_{uuid.uuid4().hex[:8]}"

        # Create anonymous user
        db_user = DbUser(
            username=username,
            is_anonymous=True,
            anonymous_token=anonymous_token,
            hashed_password=None  # No password for anonymous users
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user 