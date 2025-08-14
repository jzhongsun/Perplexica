from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from novas_app.depends import get_app_db_session
from novas_app.db.schemas import Token, UserCreate, User
from novas_app.features.auth.service import AuthService
from novas_app.features.auth.google import GoogleOAuth2
from novas_app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_password_hash
from novas_app.core.config import get_settings
from jose import jwt, JWTError

settings = get_settings()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)  # Make token optional
google_oauth = GoogleOAuth2()

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_app_db_session)
) -> Optional[User]:
    if not token:
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: Optional[str] = payload.get("sub")
        anonymous_token: Optional[str] = payload.get("anonymous_token")
        
        auth_service = AuthService(db)
        if email:
            user = await auth_service.get_user_by_email(email)
        elif anonymous_token:
            user = await auth_service.get_user_by_anonymous_token(anonymous_token)
        else:
            raise credentials_exception
            
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

@router.post("/register", response_model=User)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_app_db_session)
):
    auth_service = AuthService(db)
    return await auth_service.create_user(user_data)

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_app_db_session)
):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    from novas_app.depends import get_current_user as get_current_user_depends
    print(get_current_user_depends)
    return await get_current_user_depends() 

@router.get("/google/login")
async def google_login():
    """Get Google OAuth2 authorization URL"""
    return {"url": google_oauth.get_authorization_url()}

@router.get("/google/callback")
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_app_db_session)
):
    """Handle Google OAuth2 callback"""
    # Get access token from Google
    token_data = await google_oauth.get_access_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get access token"
        )

    # Get user info from Google
    user_info = await google_oauth.get_user_info(access_token)
    
    # Get or create user
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_email(user_info["email"])
    
    if not user:
        # Create new user with Google info
        user_data = UserCreate(
            email=user_info["email"],
            username=user_info["email"].split("@")[0],  # Use email prefix as username
            password="",  # Empty password for Google users
            full_name=user_info.get("name")
        )
        user = await auth_service.create_google_user(user_data, user_info["sub"])
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/anonymous", response_model=Token)
async def create_anonymous_session(
    user_data: Optional[UserCreate] = None,
    db: AsyncSession = Depends(get_app_db_session)
):
    """Create an anonymous user session"""
    auth_service = AuthService(db)
    user = await auth_service.create_anonymous_user(user_data)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"anonymous_token": user.anonymous_token},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_anonymous": True
    }

@router.post("/convert-anonymous", response_model=Token)
async def convert_anonymous_to_regular(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_app_db_session)
):
    """Convert an anonymous user to a regular user"""
    if not current_user or not current_user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only anonymous users can be converted"
        )
    
    auth_service = AuthService(db)
    
    # Check if email already exists
    if user_data.email:
        existing_user = await auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update anonymous user with regular user data
    current_user.email = user_data.email
    current_user.username = user_data.username
    current_user.full_name = user_data.full_name
    current_user.hashed_password = get_password_hash(user_data.password)
    current_user.is_anonymous = False
    current_user.anonymous_token = None
    
    await db.commit()
    await db.refresh(current_user)
    
    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 