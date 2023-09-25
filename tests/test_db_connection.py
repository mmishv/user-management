import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import create_async_session, get_redis


@pytest.mark.asyncio
async def test_db_connection():
    async with create_async_session() as session:
        assert isinstance(session, AsyncSession)
        async with session.begin():
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1


@pytest.mark.asyncio
async def test_redis_connection():
    async with get_redis() as redis:
        assert await redis.ping()
