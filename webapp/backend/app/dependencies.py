from typing import AsyncGenerator
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.db.session import async_session_maker

async def get_db() -> AsyncGenerator[None, None]:
    # Placeholder for get_db dependency
    # async with async_session_maker() as session:
    #     yield session
    yield None

async def get_current_user() -> dict[str, str]:
    # Placeholder for get_current_user dependency
    return {"id": "test_user_id", "role": "user"}

async def require_admin() -> dict[str, str]:
    # Placeholder for require_admin dependency
    return {"id": "test_admin_id", "role": "admin"}
