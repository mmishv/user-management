from fastapi import APIRouter, Depends, Header, HTTPException

from logs.logs import configure_logger
from src.models import User
from src.settings import Settings
from src.users.repository import UserRepository, create_user_repository
from src.users.schemas import CreateGroup, GroupInfo
from src.users.service import UserService
from src.utils import (
    admin_permission,
    get_current_user,
    has_any_permission,
    moderator_permission,
)

router = APIRouter()
logger = configure_logger(__name__)
settings = Settings()


@router.get("/healthcheck/")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"result": "You've successfully checked your health!"}


@router.get("/users/secure_data/{user_id}/")
async def get_secure_data(
    user_id: str,
    api_key: str = Header(),
    user_repo: UserRepository = Depends(create_user_repository),
):
    if api_key is None:
        raise HTTPException(status_code=401, detail="API key is missing")
    if api_key != settings.INNOTTER_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    async with user_repo as user_repository:
        user = await UserService(user_repository).get_user(user_id=user_id)

    return {"email": user.email}


@router.get("/groups/")
@has_any_permission([admin_permission])
async def groups(
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).get_all_groups()


@router.delete("/groups/{group_id}")
@has_any_permission([admin_permission])
async def groups(
    group_id: int,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).delete_group(group_id)


@router.post("/groups/", response_model=GroupInfo)
@has_any_permission([admin_permission])
async def create_group(
    create_group_data: CreateGroup,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(create_user_repository),
):
    async with user_repo as user_repository:
        return await UserService(user_repository).create_group(create_group_data)
