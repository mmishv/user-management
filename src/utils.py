from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from logs.logs import configure_logger
from src.auth.repository import create_user_repository
from src.models import User
from src.settings import Settings

logger = configure_logger(__name__)

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/refresh-token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], by="username"
) -> User:
    async with create_user_repository() as user_repo:
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
