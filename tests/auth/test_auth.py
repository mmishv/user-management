import pytest
from httpx import AsyncClient

from src.main import app
from tests.auth.fixtures import (
    LOGIN_URL,
    REFRESH_TOKEN_URL,
    SIGNUP_URL,
    client_base_url,
    create_user,
    refresh_user,
    user_login_data,
    user_signup_data,
)


@pytest.mark.asyncio
async def test_successful_user_signup(user_signup_data, truncate_tables):
    await truncate_tables
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(SIGNUP_URL, json=user_signup_data)
    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "conflicting_field, new_value",
    [("email", "another_email@gmail.com"), ("username", "another_username")],
)
async def test_duplicate_identifiers_signup(
    user_signup_data, truncate_tables, create_user, conflicting_field, new_value
):
    await truncate_tables
    await create_user
    user_with_duplicate_field = user_signup_data.copy()
    user_with_duplicate_field[conflicting_field] = new_value
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(SIGNUP_URL, json=user_with_duplicate_field)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_successful_user_login(user_login_data, truncate_tables, create_user):
    await truncate_tables
    await create_user
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(LOGIN_URL, data=user_login_data)
    assert response.status_code == 200
    response_data = response.json()
    assert "refresh_token" in response_data
    assert "access_token" in response_data


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_data",
    [
        {"username": "invalid_username", "password": "1111"},
        {"username": "adam_smith", "password": "incorrect_password"},
    ],
)
async def test_invalid_data_login(
    user_login_data, truncate_tables, create_user, invalid_data
):
    await truncate_tables
    await create_user
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            LOGIN_URL, data={**user_login_data, **invalid_data}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_successful_refresh_token(truncate_tables, create_user):
    await truncate_tables
    refresh_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {refresh_token}"},
            json={"refresh_token": refresh_token},
        )
    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert "refresh_token" in response_data


@pytest.mark.asyncio
async def test_invalid_refresh_token(truncate_tables, create_user):
    await truncate_tables
    await create_user
    refresh_token = "invalid token"
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {refresh_token}"},
            json={"refresh_token": refresh_token},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_blacklisted_refresh_token(truncate_tables, refresh_user):
    await truncate_tables
    old_refresh_token = (await refresh_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.post(
            REFRESH_TOKEN_URL,
            headers={"Authorization": f"Bearer {old_refresh_token}"},
            json={"refresh_token": old_refresh_token},
        )
    assert response.status_code == 401
