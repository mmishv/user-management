from typing import List, Optional

from fastapi import HTTPException, status

from logs.logs import configure_logger
from src.models import User
from src.users.repository import UserRepository
from src.users.schemas import UserData, UserPatchData

logger = configure_logger(__name__)


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def patch_user(
        self, user_id: str, user_patch_data: UserPatchData
    ) -> UserData:
        user = await self.user_repo.get_user_by_id(user_id)
        logger.debug(f"Start patching user {user.id}")
        message = None
        if user_patch_data.email and user_patch_data.email != user.email:
            existing_user = await self.user_repo.get_user_by_email(
                user_patch_data.email
            )
            if existing_user:
                message = f"email {user_patch_data.email}"
        if (
            not message
            and user_patch_data.username
            and user_patch_data.username
            and user_patch_data.username != user.username
        ):
            existing_user = await self.user_repo.get_user_by_username(
                user_patch_data.username
            )
            if existing_user:
                message = f"username {user_patch_data.username}"
        if (
            not message
            and user_patch_data.phone_number
            and user_patch_data.phone_number
            and user_patch_data.phone_number != user.phone_number
        ):
            existing_user = await self.user_repo.get_user_by_phone_number(
                user_patch_data.phone_number
            )
            if existing_user:
                message = f"phone number {user_patch_data.phone_number}"
        if message:
            logger.debug(f"Patch user failed: user with {message} is already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with {message} already exists",
            )
        logger.debug(f"Successful patch user {user.id}")
        user = await self.user_repo.update_user(user.id, user_patch_data)
        return UserData(**user.to_dict())

    async def delete_user(self, user_id: str):
        logger.debug(f"Start deleting user {user_id}")
        await self.user_repo.delete_user(user_id)
        logger.debug(f"Successful patch user {user_id}")

    async def get_user(self, user_id) -> UserData:
        logger.debug(f"Start getting user {user_id}")
        user = await self.user_repo.get_user_by_id(user_id)
        logger.debug(f"Successful get user {user_id}")
        return UserData(**user.to_dict())

    async def get_users(
        self,
        page: int,
        limit: int,
        filter_by_name: Optional[str],
        sort_by: Optional[str],
        order_by: Optional[str],
    ) -> List[UserData]:
        logger.debug("Start getting users")
        if not hasattr(User, str(sort_by)):
            raise HTTPException(status_code=400, detail="Invalid query parameters")
        users = await self.user_repo.get_users(
            page, limit, filter_by_name, sort_by, order_by
        )
        logger.debug("Successful get user {user_id}")
        return [UserData(**user.to_dict()) for user in users]
