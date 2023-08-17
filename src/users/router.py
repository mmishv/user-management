from fastapi import APIRouter, Header

from logs.logs import configure_logger
from src.utils import get_current_user

router = APIRouter()
logger = configure_logger(__name__)


@router.get("/me/")
async def read_users_me(token: str = Header()):
    return await get_current_user(token)
