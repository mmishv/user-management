import pytest
from httpx import AsyncClient

from src.auth.schemas import UserResetPassword
from src.main import app
from tests.fixtures import (
    RESET_PASSWORD_REQUEST_URL,
    RESET_PASSWORD_URL,
    client_base_url,
    create_user,
    reset_password_token,
    user_login_data,
    user_signup_data,
)


@pytest.mark.asyncio
async def test_successful_reset_password_send_email_stage(
    truncate_tables, user_signup_data, create_user
):
    await truncate_tables
    await create_user
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            RESET_PASSWORD_REQUEST_URL, json={"email": user_signup_data.get("email")}
        )
    assert response.status_code == 200
    response_data = response.json()
    assert "reset_link" in response_data


@pytest.mark.asyncio
async def test_invalid_email_reset_password_send_email_stage(
    truncate_tables, user_signup_data
):
    await truncate_tables
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            RESET_PASSWORD_REQUEST_URL, json={"email": user_signup_data.get("email")}
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_successful_reset_password(
    user_login_data, truncate_tables, reset_password_token
):
    await truncate_tables
    token = await reset_password_token
    new_password = "new_password"
    user_login_data["password"] = new_password
    reset_password_request = UserResetPassword(
        reset_token=token, new_password=new_password
    )
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        reset_response = await client.post(
            RESET_PASSWORD_URL, json=reset_password_request.model_dump()
        )
        check_response = await client.post("/auth/login/", data=user_login_data)
    assert reset_response.status_code == 200
    assert check_response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token_reset_password(truncate_tables):
    await truncate_tables
    token = "invalid_token"
    new_password = "new_password"
    reset_password_request = UserResetPassword(
        reset_token=token, new_password=new_password
    )
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            RESET_PASSWORD_URL, json=reset_password_request.model_dump()
        )
    assert response.status_code == 401
