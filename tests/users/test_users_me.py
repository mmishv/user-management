import pytest
from httpx import AsyncClient

from src.main import app
from src.users.schemas import UserData
from src.utils import get_current_user
from tests.fixtures import (
    client_base_url,
    create_user,
    create_user_and_admin,
    user_signup_data,
)

USERS_ME_URL = "/users/me/"


@pytest.mark.asyncio
async def test_successful_get_me(truncate_tables, create_user):
    await truncate_tables
    access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 200
    response_data = response.json()
    assert "username" in response_data


@pytest.mark.asyncio
async def test_invalid_token_get_me(truncate_tables):
    await truncate_tables
    access_token = "invalid token"
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch_data",
    [
        {},
        {"name": "new_name"},
        {"email": "adamsmith@gmail.com"},
        {"username": "adam_smith"},
        {"name": "new_name", "surname": "new_surname", "image_s3_path": "path"},
        {"email": "unique_email@example.com"},
        {"username": "unique_username"},
        {"phone_number": "unique_phone_number"},
        {
            "email": "unique_email@example.com",
            "phone_number": "unique_phone_number",
            "surname": "new_surname",
        },
    ],
)
async def test_successful_patch_me(
    truncate_tables, create_user, user_signup_data, patch_data
):
    await truncate_tables
    access_token = (await create_user)[0]
    user = await get_current_user(access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.patch(
            USERS_ME_URL, headers={"token": access_token}, json=patch_data
        )

    assert response.status_code == 200

    response_data = response.json()
    for field, value in patch_data.items():
        if value:
            setattr(user, field, value)
    user.modified_at = response_data.get("modified_at")

    assert (
        UserData(**user.to_dict()).model_dump()
        == UserData(**response_data).model_dump()
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch_data",
    [
        {"email": "adamsmith@gmail.com"},
        {"username": "adam_smith"},
    ],
)
async def test_duplicate_data_patch_me(
    truncate_tables, create_user_and_admin, patch_data
):
    await truncate_tables
    admin_access_token = (await create_user_and_admin)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.patch(
            USERS_ME_URL, headers={"token": admin_access_token}, json=patch_data
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_invalid_token_patch_me(truncate_tables):
    await truncate_tables
    access_token = "invalid token"
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.patch(
            USERS_ME_URL, headers={"token": access_token}, json={}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_successful_delete_me(truncate_tables, create_user):
    await truncate_tables
    access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.delete(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_repetitive_delete_me(truncate_tables, create_user):
    await truncate_tables
    access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        await client.delete(USERS_ME_URL, headers={"token": access_token})
        response = await client.delete(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_delete_me(truncate_tables):
    await truncate_tables
    access_token = "invalid token"
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.delete(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 401
