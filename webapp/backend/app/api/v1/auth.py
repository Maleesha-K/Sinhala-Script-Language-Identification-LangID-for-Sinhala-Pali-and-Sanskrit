from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Login, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

from app.db.models.user import User

from app.schemas.response import BaseResponse, success_response

@router.post("/signup", response_model=BaseResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """Register a new user."""
    user = await user_service.create_user(db, user_in)
    return success_response(data=user, message="User registered successfully")

@router.post("/login", response_model=BaseResponse[Token])
async def login(credentials: Login, db: AsyncSession = Depends(get_db)) -> dict:
    """Authenticate a user and return access & refresh tokens."""
    user = await auth_service.authenticate(db, credentials)
    tokens = auth_service.create_tokens(user)
    return success_response(data=tokens, message="Login successful")

from app.schemas.auth import TokenRefresh

@router.post("/refresh", response_model=BaseResponse[Token])
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)) -> dict:
    """Refresh an access token using a valid refresh token."""
    tokens = await auth_service.refresh_tokens(db, token_data.refresh_token)
    return success_response(data=tokens, message="Tokens refreshed successfully")
