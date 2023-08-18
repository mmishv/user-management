from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import create_async_session, get_redis
from src.models import User


class BaseUserRepository:
    def __init__(self, db_session: AsyncSession, redis_session=None):
        self.db_session = db_session
        self.redis_session = redis_session

    async def get_user_by_username(self, username: str) -> Optional[User]:
        async with self.db_session as conn:
            user = await conn.execute(select(User).filter(User.username == username))
        return user.scalar()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self.db_session as conn:
            user = await conn.execute(select(User).filter(User.email == email))
        return user.scalar()

    async def get_user_by_phone_number(self, phone_number: str) -> Optional[User]:
        async with self.db_session as conn:
            user = await conn.execute(
                select(User).filter(User.phone_number == phone_number)
            )
        return user.scalar()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        async with self.db_session as conn:
            user = await conn.execute(select(User).filter(User.id == user_id))
        return user.scalar()

    async def check_if_token_is_blacklisted(self, token: str) -> bool:
        async with self.redis_session as conn:
            token_value = await conn.get(token)
        return token_value is not None


@asynccontextmanager
async def create_base_user_repository() -> AsyncGenerator[BaseUserRepository, None]:
    async with create_async_session() as db_session:
        async with get_redis() as redis_session:
            yield BaseUserRepository(db_session, redis_session)
