from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import create_async_session, get_redis
from src.models import User


class AuthRepository:
    def __init__(self, db_session: AsyncSession, redis_session):
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

    async def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        async with self.db_session as conn:
            conn.add(user)
            await conn.commit()
        return user

    async def update_password(self, user_id: int, new_password: str):
        async with self.db_session as conn:
            user = await conn.get(User, user_id)
            user.hashed_password = new_password
            await conn.commit()

    async def blacklist_refresh_token(self, token: str, expire_time_in_days: int):
        expire_time_in_seconds = expire_time_in_days * 86400
        async with self.redis_session as conn:
            await conn.setex(token, expire_time_in_seconds, token)

    async def blacklist_reset_token(self, token: str, expire_time_in_minutes: int):
        expire_time_in_seconds = expire_time_in_minutes * 60
        async with self.redis_session as conn:
            await conn.setex(token, expire_time_in_seconds, token)

    async def check_if_token_is_blacklisted(self, token: str) -> bool:
        async with self.redis_session as conn:
            token_value = await conn.get(token)
        return token_value is not None


@asynccontextmanager
async def create_user_repository() -> AsyncGenerator[AuthRepository, None]:
    async with create_async_session() as db_session:
        async with get_redis() as redis_session:
            yield AuthRepository(db_session, redis_session)
