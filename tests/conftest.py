import asyncio
from typing import Generator

import pytest

from src.aws.email_service import SESEmailService
from src.aws.user_image_service import S3UserImageService
from src.database import engine
from src.models import Base


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def truncate_tables():
    await S3UserImageService().delete_all_avatars()
    await SESEmailService().verify_email("sender@example.com")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
