from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import Login, Token
from app.services.user_service import user_service
from app.utils.security import verify_password, create_access_token, create_refresh_token
from app.utils.exceptions import UnauthorizedException
from app.db.models.user import User

class AuthService:
    async def authenticate(self, db: AsyncSession, credentials: Login) -> User:
        user = await user_service.get_by_email(db, email=credentials.email)
        if not user:
            raise UnauthorizedException(message="Incorrect email or password")
        if not verify_password(credentials.password, user.password_hash):
            raise UnauthorizedException(message="Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedException(message="Inactive user")
        return user
        
    def create_tokens(self, user: User) -> Token:
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def refresh_tokens(self, db: AsyncSession, refresh_token: str) -> Token:
        from jose import jwt, JWTError
        from app.config import settings
        import uuid
        
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str: str | None = payload.get("sub")
            token_type: str | None = payload.get("type")
            
            if user_id_str is None or token_type != "refresh":
                raise UnauthorizedException(message="Invalid refresh token")
                
            user_id = uuid.UUID(user_id_str)
        except (JWTError, ValueError):
            raise UnauthorizedException(message="Invalid refresh token")
            
        user = await user_service.get_by_id(db, user_id=user_id)
        if not user:
            raise UnauthorizedException(message="User not found")
        if not user.is_active:
            raise UnauthorizedException(message="Inactive user")
            
        return self.create_tokens(user)

auth_service = AuthService()
