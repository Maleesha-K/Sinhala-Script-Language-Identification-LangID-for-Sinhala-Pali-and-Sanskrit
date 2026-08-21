from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserResponse, UserUpdate
from app.db.models.user import User
from app.services.user_service import user_service
from app.dependencies import get_db, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

from app.schemas.response import BaseResponse, success_response

@router.get("/me", response_model=BaseResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)) -> dict:
    """Get the current authenticated user's profile."""
    return success_response(data=current_user, message="Profile retrieved")

@router.patch("/me", response_model=BaseResponse[UserResponse])
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update the current authenticated user's profile."""
    updated_user = await user_service.update_user(db, user_id=current_user.id, user_in=user_in)
    return success_response(data=updated_user, message="Profile updated successfully")
