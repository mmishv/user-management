from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aioredis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from logs.logs import configure_logger
from src.settings import Settings

logger = configure_logger(__name__)

settings = Settings()

SQLALCHEMY_DATABASE_URL = settings.POSTGRES_URL_SQLALCHEMY
DATABASE_URL = settings.POSTGRES_URL
REDIS_URL = settings.REDIS_URL

engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, echo=True, future=True, pool_size=10, max_overflow=20
)


@asynccontextmanager
async def create_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as transaction:
        async_session_maker = sessionmaker(
            class_=AsyncSession, expire_on_commit=False, bind=transaction
        )
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()


@asynccontextmanager
async def get_redis():
    redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()
