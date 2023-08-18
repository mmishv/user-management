from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional, Sequence, Tuple, Type

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import create_async_session
from src.models import User
from src.repository import BaseUserRepository
from src.users.schemas import UserData, UserPatchData


class UserRepository(BaseUserRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def update_user(self, user_id, user_data: UserPatchData) -> Type[User] | None:
        async with self.db_session as conn:
            user = await conn.get(User, user_id)
            for field, value in user_data.model_dump().items():
                if value:
                    setattr(user, field, value)
            user.modified_at = datetime.now()
            await conn.commit()
        return user

    async def delete_user(self, user_id):
        async with self.db_session as conn:
            user = await conn.get(User, user_id)
            await conn.delete(user)
            await conn.commit()

    async def get_users(
        self,
        page: int,
        limit: int,
        filter_by_name: Optional[str],
        sort_by: Optional[str],
        order_by: Optional[str],
    ) -> Sequence[User]:
        query = select(User)

        if filter_by_name:
            query = query.filter(User.name.ilike(f"%{filter_by_name}%"))

        if sort_by:
            if order_by.lower() == "asc":
                query = query.order_by(getattr(User, sort_by))
            elif order_by.lower() == "desc":
                query = query.order_by(getattr(User, sort_by).desc())

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        async with self.db_session as session:
            async with session.begin():
                result = await session.execute(query.options(selectinload(User.group)))
                users = result.scalars().all()

        return users


@asynccontextmanager
async def create_user_repository() -> AsyncGenerator[UserRepository, None]:
    async with create_async_session() as db_session:
        yield UserRepository(db_session)
