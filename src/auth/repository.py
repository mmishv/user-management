from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import UserSignup
from src.database import create_async_session, get_redis
from src.models import User
from src.repository import BaseUserRepository


class AuthRepository(BaseUserRepository):
    def __init__(self, db_session: AsyncSession, redis_session):
        super().__init__(db_session, redis_session)

    async def create_user(self, user_data: UserSignup) -> User:
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=user_data.password,
        )
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


@asynccontextmanager
async def create_auth_repository() -> AsyncGenerator[AuthRepository, None]:
    async with create_async_session() as db_session:
        async with get_redis() as redis_session:
            yield AuthRepository(db_session, redis_session)
