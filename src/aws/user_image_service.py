import base64

import aioboto3
from fastapi import HTTPException, UploadFile

from logs.logs import configure_logger
from src.settings import Settings

logger = configure_logger(__name__)
settings = Settings()


class S3UserImageService:
    BUCKET = "user-avatars"
    CONTENTS_KEY = "Contents"

    def __init__(self):
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.endpoint_url = settings.ENDPOINT_URL

    async def _s3_session(self):
        return aioboto3.Session(
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        )

    async def _perform_s3_action(self, action_callback):
        session = await self._s3_session()
        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            try:
                await self._create_bucket_if_not_exists(s3)
                return await action_callback(s3)
            except Exception as e:
                logger.error(f"S3 action error: {e} ({type(e)})")
                raise HTTPException(status_code=500, detail="Error interacting with S3")

    async def upload_avatar(self, file: UploadFile, user_id: str):
        async def upload_to_s3(s3):
            file_path = f"avatars/{user_id}"
            await s3.upload_fileobj(file, self.BUCKET, file_path)
            return file_path

        return await self._perform_s3_action(upload_to_s3)

    async def get_avatar(self, avatar_s3_path: str):
        async def get_from_s3(s3):
            s3_ob = await s3.get_object(Bucket=self.BUCKET, Key=avatar_s3_path)
            image_bytes = await s3_ob["Body"].read()
            return base64.b64encode(image_bytes).decode("utf-8")

        return await self._perform_s3_action(get_from_s3)

    async def delete_avatar(self, avatar_s3_path: str):
        async def delete_from_s3(s3):
            await s3.delete_object(Bucket=self.BUCKET, Key=avatar_s3_path)

        await self._perform_s3_action(delete_from_s3)

    async def delete_all_avatars(self):
        async def delete_all_objects(s3):
            objects = await s3.list_objects(Bucket=self.BUCKET)
            if self.CONTENTS_KEY in objects:
                for obj in objects[self.CONTENTS_KEY]:
                    await s3.delete_object(Bucket=self.BUCKET, Key=obj["Key"])

        await self._perform_s3_action(delete_all_objects)

    async def _create_bucket_if_not_exists(self, s3):
        try:
            await s3.head_bucket(Bucket=self.BUCKET)
            logger.info(f"Bucket '{self.BUCKET}' already exists.")
        except s3.exceptions.ClientError:
            try:
                await s3.create_bucket(Bucket=self.BUCKET)
                logger.info(f"Bucket '{self.BUCKET}' created successfully.")
            except Exception as e:
                logger.error(f"Error creating bucket '{self.BUCKET}': {e} ({type(e)})")
                raise
        except Exception as e:
            logger.error(f"Error checking bucket '{self.BUCKET}': {e} ({type(e)})")
            raise
