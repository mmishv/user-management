import pytest
from httpx import AsyncClient

from src.main import app
from tests.fixtures import client_base_url, create_user, user_signup_data

USERS_ME_URL = "/users/me/"


@pytest.mark.asyncio
async def test_successful_get_me(truncate_tables, create_user):
    await truncate_tables
    access_token = (await create_user)[0]
    async with AsyncClient(app=app, base_url=client_base_url) as client:
        response = await client.get(USERS_ME_URL, headers={"token": access_token})
    assert response.status_code == 200
