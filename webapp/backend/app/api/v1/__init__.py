from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
