from datetime import datetime

import pytest
from httpx import AsyncClient

from src.auth.schemas import UserLogin, UserSignup
from src.database import create_async_session
from src.main import app
from src.models import Group, User
from src.utils import get_current_user

client_base_url = "http://test"

SIGNUP_URL = "/auth/signup/"
LOGIN_URL = "/auth/login/"
REFRESH_TOKEN_URL = "/auth/refresh-token/"
RESET_PASSWORD_REQUEST_URL = "/auth/reset-password-request/"
RESET_PASSWORD_URL = "/auth/reset-password/"


@pytest.fixture
def user_signup_data():
    return UserSignup(
        username="adam_smith", email="adamsmith@gmail.com", password="1111"
    ).model_dump()


@pytest.fixture
def user_login_data():
    return UserLogin(username="adam_smith", password="1111").model_dump()


@pytest.fixture
@pytest.mark.asyncio
async def create_user(user_signup_data):
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(SIGNUP_URL, json=user_signup_data)
    refresh_token = response.json().get("refresh_token")
    access_token = response.json().get("access_token")
    return access_token, refresh_token


@pytest.fixture
@pytest.mark.asyncio
async def refresh_user(create_user):
    old_refresh_token = (await create_user)[1]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            REFRESH_TOKEN_URL,
            headers={"token": old_refresh_token},
        )
    new_refresh_token = response.json().get("refresh_token")
    return old_refresh_token, new_refresh_token


@pytest.fixture
@pytest.mark.asyncio
async def reset_password_token(user_signup_data, create_user):
    await create_user
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            RESET_PASSWORD_REQUEST_URL, json={"email": user_signup_data.get("email")}
        )
    link = response.json().get("reset_link")
    token = link.split("=")[-1]
    return token


@pytest.fixture
@pytest.mark.asyncio
async def create_user_and_admin(create_user):
    user_access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            SIGNUP_URL,
            json=UserSignup(
                username="admin", email="admin@gmail.com", password="1111"
            ).model_dump(),
        )
    admin_access_token = response.json().get("access_token")
    admin = await get_current_user(admin_access_token)
    async with create_async_session() as conn:
        admin = await conn.get(User, admin.id)
        admin.role = "ADMIN"
        await conn.commit()
    return admin_access_token, user_access_token


@pytest.fixture
@pytest.mark.asyncio
async def create_user_and_moderator_from_the_same_group(create_user):
    user_access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            SIGNUP_URL,
            json=UserSignup(
                username="moderator", email="moderator@gmail.com", password="1111"
            ).model_dump(),
        )
    access_token = response.json().get("access_token")
    user = await get_current_user(user_access_token)
    moderator = await get_current_user(access_token)
    async with create_async_session() as conn:
        group = Group(name="first_group", created_at=datetime.utcnow())
        conn.add(group)
        await conn.commit()
        user = await conn.get(User, user.id)
        user.group_id = group.id
        moderator = await conn.get(User, moderator.id)
        moderator.group_id = group.id
        await conn.commit()
    return access_token, user_access_token


@pytest.fixture
@pytest.mark.asyncio
async def create_user_and_moderator_from_diff_group(
    create_user_and_moderator_from_the_same_group,
):
    (
        moderator_access_token,
        user_access_token,
    ) = await create_user_and_moderator_from_the_same_group
    moderator = await get_current_user(moderator_access_token)
    async with create_async_session() as conn:
        group = Group(name="second_group", created_at=datetime.utcnow())
        conn.add(group)
        await conn.commit()
        moderator = await conn.get(User, moderator.id)
        moderator.group_id = group.id
        await conn.commit()
    return moderator_access_token, user_access_token
