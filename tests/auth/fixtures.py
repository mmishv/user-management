import pytest
from httpx import AsyncClient

from src.auth.schemas import UserLogin, UserSignup
from src.main import app

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
    old_refresh_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {old_refresh_token}"},
            json={"refresh_token": old_refresh_token},
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
