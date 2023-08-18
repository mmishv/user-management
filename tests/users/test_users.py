import pytest
from httpx import AsyncClient

from src.main import app
from src.users.schemas import UserData
from src.utils import get_current_user
from tests.fixtures import (
    client_base_url,
    create_user,
    create_user_and_admin,
    create_user_and_moderator_from_diff_group,
    create_user_and_moderator_from_the_same_group,
    user_signup_data,
)

USERS_URL = "/users"


@pytest.mark.parametrize(
    "tokens_fixture",
    ["create_user_and_admin", "create_user_and_moderator_from_the_same_group"],
)
@pytest.mark.asyncio
async def test_successful_get_user(tokens_fixture, truncate_tables, request):
    await truncate_tables
    admin_access_token, user_access_token = await request.getfixturevalue(
        tokens_fixture
    )
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(
            f"{USERS_URL}/{user.id}/", headers={"token": admin_access_token}
        )
    assert response.status_code == 200

    response_data = response.json()
    assert (
        UserData(**user.to_dict()).model_dump()
        == UserData(**response_data).model_dump()
    )


@pytest.mark.parametrize(
    "tokens_fixture", ["create_user", "create_user_and_moderator_from_diff_group"]
)
@pytest.mark.asyncio
async def test_no_permissions_get_user(tokens_fixture, truncate_tables, request):
    await truncate_tables
    admin_access_token, user_access_token = await request.getfixturevalue(
        tokens_fixture
    )
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(
            f"{USERS_URL}/{user.id}/", headers={"token": admin_access_token}
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_successful_patch_user(truncate_tables, create_user_and_admin):
    await truncate_tables
    admin_access_token, user_access_token = await create_user_and_admin
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.patch(
            f"{USERS_URL}/{user.id}/", headers={"token": admin_access_token}, json={}
        )

    assert response.status_code == 200

    response_data = response.json()
    user.modified_at = response_data.get("modified_at")
    assert (
        UserData(**user.to_dict()).model_dump()
        == UserData(**response_data).model_dump()
    )


@pytest.mark.parametrize(
    "tokens_fixture",
    [
        "create_user",
        "create_user_and_moderator_from_the_same_group",
        "create_user_and_moderator_from_diff_group",
    ],
)
@pytest.mark.asyncio
async def test_no_permissions_patch_user(tokens_fixture, truncate_tables, request):
    await truncate_tables
    admin_access_token, user_access_token = await request.getfixturevalue(
        tokens_fixture
    )
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.patch(
            f"{USERS_URL}/{user.id}/", headers={"token": admin_access_token}, json={}
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_successful_delete_user(truncate_tables, create_user_and_admin):
    await truncate_tables
    admin_access_token, user_access_token = await create_user_and_admin
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.delete(
            f"{USERS_URL}/{user.id}/", headers={"token": admin_access_token}
        )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "tokens_fixture",
    [
        "create_user",
        "create_user_and_moderator_from_the_same_group",
        "create_user_and_moderator_from_diff_group",
    ],
)
@pytest.mark.asyncio
async def test_no_permissions_delete_user(tokens_fixture, truncate_tables, request):
    await truncate_tables
    access_token, user_access_token = await request.getfixturevalue(tokens_fixture)
    user = await get_current_user(user_access_token)
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.delete(
            f"{USERS_URL}/{user.id}/", headers={"token": access_token}
        )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ("?page=5&limit=30&sort_by=name&order_by=desc", 200),
        ("?page=1&limit=30&sort_by=id&order_by=asc", 200),
        ("?page=1&limit=30&sort_by=id&order_by=desc", 200),
        ("?page=-1&limit=30&sort_by=id&order_by=desc", 400),
        ("?page=1&limit=300&sort_by=id&order_by=desc", 400),
        ("?page=1&limit=30&sort_by=invalid_field", 403),
        ("?page=1&limit=30&order_by=invalid_order", 403),
    ],
)
@pytest.mark.asyncio
async def test_successful_get_users(
    truncate_tables, query_params, expected_status, create_user_and_admin
):
    await truncate_tables
    admin_access_token = (await create_user_and_admin)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(
            f"{USERS_URL}/{query_params}/", headers={"token": admin_access_token}
        )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ("?page=5&limit=30&sort_by=name&order_by=desc", 200),
        ("?page=1&limit=30&sort_by=id&order_by=asc", 200),
        ("?page=1&limit=30&sort_by=id&order_by=desc", 200),
        ("?page=-1&limit=30", 422),
        ("?page=1&limit=150", 422),
        ("?page=1&limit=30&sort_by=invalid_field", 403),
        ("?page=1&limit=30&order_by=invalid_order", 403),
    ],
)
@pytest.mark.asyncio
async def test_successful_get_users(
    truncate_tables, query_params, expected_status, create_user_and_admin
):
    await truncate_tables
    admin_access_token = (await create_user_and_admin)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(
            f"{USERS_URL}/{query_params}/", headers={"token": admin_access_token}
        )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "tokens_fixture",
    [
        "create_user",
        "create_user_and_moderator_from_the_same_group",
        "create_user_and_moderator_from_diff_group",
    ],
)
@pytest.mark.asyncio
async def test_no_permissions_get_users(tokens_fixture, truncate_tables, request):
    await truncate_tables
    access_token = (await request.getfixturevalue(tokens_fixture))[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(
            f"{USERS_URL}/?page=5&limit=30&sort_by=name&order_by=desc/",
            headers={"token": access_token},
        )
    assert response.status_code == 403
