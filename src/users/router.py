from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile

from logs.logs import configure_logger
from src.models import User
from src.users.repository import UserRepository, create_user_repository
from src.users.schemas import (
    UserData,
    UserPatchData,
    UserPatchDataAdvanced,
    UserUUIDList,
)
from src.users.service import UserService
from src.utils import (
    admin_permission,
    get_current_user,
    has_any_permission,
    moderator_group_permission,
    moderator_permission,
)

router = APIRouter()
logger = configure_logger(__name__)


@router.get("/me/", response_model=UserData)
async def read_me(
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).get_user(user_id=user.id)


@router.patch("/me/", response_model=UserData)
async def update_me(
    user_patch_data: UserPatchData = Depends(),
    avatar: UploadFile = File(None),
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).patch_user(
            user_id=user.id, user_patch_data=user_patch_data, avatar=avatar
        )


@router.delete("/me/")
async def delete_me(
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).delete_user(user_id=user.id)


@router.get("/{user_id}/", response_model=UserData)
# @has_any_permission([moderator_group_permission, admin_permission])
async def read_user(
    user_id: str,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).get_user(user_id=user_id)


@router.patch("/{user_id}/", response_model=UserData)
@has_any_permission([admin_permission, moderator_group_permission])
async def patch_user(
    user_id: str,
    user_patch_data: UserPatchDataAdvanced = Depends(),
    avatar: UploadFile = File(None),
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).patch_user(
            user_id=user_id, user_patch_data=user_patch_data, avatar=avatar
        )


@router.delete("/{user_id}/")
@has_any_permission([admin_permission])
async def delete_user(
    user_id: str,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).delete_user(user_id=user_id)


@router.get("/", response_model=List[UserData])
@has_any_permission([admin_permission, moderator_permission])
async def get_users(
    user: User = Depends(get_current_user),
    page: Optional[int] = Query(1, description="Page number", gt=0),
    limit: Optional[int] = Query(
        30, description="Number of items per page", gt=0, le=100
    ),
    filter_by_name: Optional[str] = Query(None, description="Filter users by name"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    order_by: Optional[str] = Query(
        "asc", description="Sorting order ('asc' or 'desc')"
    ),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).get_users(
            page, limit, filter_by_name, sort_by, order_by, user
        )


@router.post("/list/", response_model=List[UserData])
async def users_list(
    user_uuid_list: UserUUIDList,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).get_users_by_uuid_list(user_uuid_list)
