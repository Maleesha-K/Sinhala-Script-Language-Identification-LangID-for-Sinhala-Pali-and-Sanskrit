from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import uuid

from app.db.session import async_session_maker
from app.config import settings
from app.utils.exceptions import UnauthorizedException, ForbiddenException
from app.db.models.user import User, UserRole
from app.services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        
        if user_id_str is None or token_type != "access":
            raise UnauthorizedException()
            
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedException()
        
    user = await user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise UnauthorizedException(message="User not found")
    if not user.is_active:
        raise UnauthorizedException(message="Inactive user")
    return user

async def get_ws_current_user(token: str, db: AsyncSession = Depends(get_db)) -> User:
    """Dependency for authenticating WebSocket connections via query parameter"""
    if not token:
        raise ValueError("Missing token")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise ValueError("Invalid token")
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise ValueError("Invalid token")
        
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")
    if not user.is_active:
        raise ValueError("User inactive")
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException(message="Admin privileges required")
    return current_user
