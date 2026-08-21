from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router

from contextlib import asynccontextmanager
from app.db.session import async_session_maker
from app.db.models.user import User, UserRole
from app.utils.security import get_password_hash
from sqlalchemy import select

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create initial admin if configured
    if settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_PASSWORD:
        async with async_session_maker() as session:
            result = await session.execute(select(User).where(User.email == settings.INITIAL_ADMIN_EMAIL))
            admin = result.scalar_one_or_none()
            if not admin:
                new_admin = User(
                    email=settings.INITIAL_ADMIN_EMAIL,
                    password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                    display_name="Admin"
                )
                session.add(new_admin)
                await session.commit()
                print(f"Created initial admin user: {settings.INITIAL_ADMIN_EMAIL}")
    yield
    # Shutdown logic can go here

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    from app.utils.exceptions import AppException
    from app.schemas.response import error_response

    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message=exc.detail),
            headers=getattr(exc, "headers", None)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response(message="Validation error", data=exc.errors())
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=error_response(message="Internal server error")
        )

    @app.get("/health", tags=["healthcheck"])
    async def health_check():
        return {"status": "ok"}

    return app

app = create_app()
