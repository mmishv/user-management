from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status

from logs.logs import configure_logger
from src.auth.repository import AuthRepository
from src.auth.schemas import (
    JwtRequest,
    JwtResponse,
    UserLogin,
    UserResetPassword,
    UserSignup,
)
from src.aws.email_service import SESEmailService
from src.models import User
from src.settings import Settings
from src.utils import get_current_user

logger = configure_logger(__name__)
settings = Settings()


class AuthService:
    def __init__(self, user_repo: AuthRepository):
        self.user_repo = user_repo

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        logger.debug(f"Starting user {username} authentication")
        user = await self.user_repo.get_user_by_username(username)
        if not user:
            logger.debug("User authentication failed: invalid username")
            return None
        if not verify_password(password, user.hashed_password):
            logger.debug(f"User {username} authentication failed: invalid password")
            return None
        logger.debug(f"Successful authentication: user {username} found")
        return user

    async def signup(self, user: UserSignup) -> JwtResponse:
        logger.debug("Starting signup")
        existing_user_with_username = await self.user_repo.get_user_by_username(
            user.username
        )
        existing_user_with_email = await self.user_repo.get_user_by_email(user.email)
        if existing_user_with_username:
            logger.debug(
                f"Signup failed: user with username {user.username} is already exists"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with username '{user.username}' already exists",
            )
        if existing_user_with_email:
            logger.debug(
                f"Signup failed: user with email {user.email} is already exists"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user.email}' already exists",
            )
        hashed_password = get_password_hash(user.password)
        user_data = {
            "email": user.email,
            "password": hashed_password,
            "username": user.username,
        }
        user = await self.user_repo.create_user(UserSignup(**user_data))
        jwt_request = JwtRequest(
            username=user.username,
            user_id=str(user.id),
            role=user.role,
            is_blocked=user.is_blocked,
        ).model_dump()
        access_token, refresh_token = create_access_token(
            jwt_request
        ), create_refresh_token(jwt_request)
        logger.debug(f"Successful signup: user {user.username} created")
        return JwtResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, user: UserLogin) -> JwtResponse:
        logger.debug(f"Starting user {user.username} login")
        user = await self.authenticate_user(
            username=user.username, password=user.password
        )
        if user is None:
            logger.debug("Login failed: invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        jwt_request = JwtRequest(
            username=user.username,
            user_id=str(user.id),
            role=user.role,
            is_blocked=user.is_blocked,
        ).model_dump()
        access_token, refresh_token = (
            create_access_token(jwt_request),
            create_refresh_token(jwt_request),
        )
        logger.debug(f"Successful {user.username} login")
        return JwtResponse(access_token=access_token, refresh_token=refresh_token)

    async def send_reset_password_email(self, email: str) -> str:
        logger.debug(f"Sending reset password email for {email}")
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            logger.debug("Reset password failed: user not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email. No user found with this email address",
            )
        reset_token = create_reset_password_token(email)
        link = f"http://python:8000/reset-password?reset_password_token={reset_token}"
        email_service = SESEmailService()
        await email_service.send_email(
            subject="Reset password email",
            body=link,
            sender="sender@example.com",
            recipient=email,
        )
        logger.debug(f"Sending reset password email to: {email} with link: {link}")
        return link

    async def reset_password(self, data: UserResetPassword):
        user = await get_current_user(data.reset_token, by="email")
        logger.debug(f"Starting user {user.username} resetting password")
        await self.user_repo.blacklist_reset_token(
            data.reset_token, settings.RESET_TOKEN_EXPIRE_MINUTES
        )
        hashed_password = get_password_hash(data.new_password)
        await self.user_repo.update_password(
            user_id=user.id, new_password=hashed_password
        )
        logger.debug(f"{user.email} reset password successfully")

    async def get_new_tokens(self, refresh_token: str) -> JwtResponse:
        user = await get_current_user(refresh_token)
        logger.debug(f"Starting user {user.username} refreshing tokens")
        await self.user_repo.blacklist_refresh_token(
            refresh_token, settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        jwt_request = JwtRequest(
            username=user.username,
            user_id=str(user.id),
            role=user.role,
            is_blocked=user.is_blocked,
        ).model_dump()
        access_token, refresh_token = (
            create_access_token(jwt_request),
            create_refresh_token(jwt_request),
        )
        logger.debug(f"{user.email} refreshed tokens successfully")
        return JwtResponse(access_token=access_token, refresh_token=refresh_token)


def verify_password(password, hashed_password) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expiration = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expiration})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_reset_password_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.utcnow()
        + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
        "type": "reset",
    }
    reset_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return reset_token
