from typing import Annotated

from fastapi import APIRouter, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm

from logs.logs import configure_logger
from src.auth.repository import AuthRepository, create_user_repository
from src.auth.schemas import (
    JwtResponse,
    UserEmail,
    UserLogin,
    UserResetPassword,
    UserSignup,
)
from src.auth.service import AuthService

router = APIRouter()
logger = configure_logger(__name__)


@router.post("/signup/", response_model=JwtResponse)
async def signup(
    user: UserSignup, user_repo: AuthRepository = Depends(create_user_repository)
):
    logger.info("Signup endpoint accessed")
    async with user_repo as user_repository:
        result = await AuthService(user_repository).signup(user)
        return result


@router.post("/login/", response_model=JwtResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: AuthRepository = Depends(create_user_repository),
):
    logger.info("Login endpoint accessed")
    user = UserLogin(username=form_data.username, password=form_data.password)
    async with user_repo as user_repository:
        return await AuthService(user_repository).login(user)


@router.post("/refresh-token/", response_model=JwtResponse)
async def refresh_token(
    token: str = Header(),
    user_repo: AuthRepository = Depends(create_user_repository),
):
    logger.info("Refresh endpoint accessed")
    async with user_repo as user_repository:
        result = await AuthService(user_repository).get_new_tokens(token)
    return result


@router.post("/reset-password-request/")
async def reset_password_request(
    reset_request: UserEmail,
    user_repo: AuthRepository = Depends(create_user_repository),
):
    logger.info("Reset password (send email stage) endpoint accessed")
    async with user_repo as user_repository:
        link = await AuthService(user_repository).send_reset_password_email(
            reset_request.email
        )
    return {"message": "Password reset email sent", "reset_link": link}


@router.post("/reset-password/")
async def reset_password(
    data: UserResetPassword, user_repo: AuthRepository = Depends(create_user_repository)
):
    logger.info("Reset password (set new password stage) endpoint accessed")
    async with user_repo as user_repository:
        await AuthService(user_repository).reset_password(data)
    return {"message": "Password reset successful"}
