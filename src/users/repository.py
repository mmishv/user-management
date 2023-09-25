from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Optional, Sequence, Type

from fastapi import File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.aws.user_image_service import S3UserImageService
from src.database import create_async_session
from src.models import User
from src.repository import BaseUserRepository
from src.users.schemas import UserPatchDataAdvanced


class UserRepository(BaseUserRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)

    async def update_user(
        self, user_id, user_data: UserPatchDataAdvanced, avatar: File
    ) -> Type[User] | None:
        async with self.db_session as conn:
            user = await conn.get(User, user_id)
            if avatar:
                avatar_service = S3UserImageService()
                if user.image_s3_path:
                    await avatar_service.delete_avatar(str(user.image_s3_path))
                new_avatar_s3_path = await avatar_service.upload_avatar(avatar, user.id)
                user.image_s3_path = new_avatar_s3_path
            for field, value in user_data.model_dump().items():
                if value is not None:
                    setattr(user, field, value)
            user.modified_at = datetime.now()
            await conn.commit()
        return user

    async def delete_user(self, user_id):
        async with self.db_session as conn:
            user = await conn.get(User, user_id)
            if user.image_s3_path:
                await S3UserImageService().delete_avatar(str(user.image_s3_path))
            await conn.delete(user)
            await conn.commit()

    async def get_users(
        self,
        page: int,
        limit: int,
        filter_by_name: Optional[str],
        sort_by: Optional[str],
        order_by: Optional[str],
        group_id: int = None,
    ) -> Sequence[User]:
        query = select(User)

        if group_id:
            query = query.filter(User.group_id == group_id)

        if filter_by_name:
            query = query.filter(User.username.ilike(f"%{filter_by_name}%"))

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
