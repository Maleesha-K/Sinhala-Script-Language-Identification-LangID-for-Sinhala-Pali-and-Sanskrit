from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router
from app.api.v1.documents import router as documents_router
from app.api.v1.classification import router as classification_router

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(admin_router)
v1_router.include_router(documents_router)
v1_router.include_router(classification_router)
