import inspect
from functools import wraps
from typing import List

import jwt
from fastapi import Header, HTTPException, status

from logs.logs import configure_logger
from src.models import User
from src.repository import create_base_user_repository
from src.settings import Settings

logger = configure_logger(__name__)

settings = Settings()


async def get_current_user(token: str = Header(), by="username") -> User:
    async with create_base_user_repository() as user_repo:
        is_blacklisted = await user_repo.check_if_token_is_blacklisted(token)
        if is_blacklisted:
            raise HTTPException(status_code=401, detail="Token is blacklisted")
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            sub: str = payload.get(by)
        except jwt.exceptions.DecodeError:
            logger.debug("JWT processing decode error: invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
        except jwt.exceptions.ExpiredSignatureError:
            logger.debug("JWT processing error: expired token")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.exceptions.PyJWTError:
            logger.debug("JWT processing error")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        user = (
            await user_repo.get_user_by_username(username=sub)
            if by == "username"
            else await user_repo.get_user_by_email(email=sub)
        )
        if user is None:
            logger.debug("JWT credentials error: user not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        return user


def admin_permission(user_id: str, user: User):
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=401,
            detail="You have not enough privileges: you must be an administrator",
        )


def moderator_permission(user_id: str, user: User):
    if user.role != "MODERATOR":
        raise HTTPException(
            status_code=401,
            detail="You have not enough privileges: you must be a moderator",
        )


async def moderator_group_permission(user_id: str, user: User):
    async with create_base_user_repository() as user_repo:
        user_info = await user_repo.get_user_by_id(user_id=user_id)

    if (
        user.role != "MODERATOR"
        or not user_info.group_id
        or user_info.group_id != user.group_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Users and moderators must belong to the same group.",
        )


def has_any_permission(permissions: List[callable]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id, user = kwargs.get("user_id"), kwargs.get("user")
            for permission in permissions:
                try:
                    if inspect.iscoroutinefunction(permission):
                        await permission(user_id, user)
                    else:
                        permission(user_id, user)
                    return await func(*args, **kwargs)
                except HTTPException:
                    continue

            raise HTTPException(
                status_code=403,
                detail="Access denied. You must have at least one of the required permissions",
            )

        return wrapper

    return decorator
