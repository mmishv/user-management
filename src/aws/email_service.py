from aioboto3 import Session
from fastapi import HTTPException

from logs.logs import configure_logger
from src.settings import Settings

settings = Settings()
logger = configure_logger(__name__)


class SESEmailService:
    def __init__(self):
        self.aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        self.region_name = "us-east-1"

    async def _ses_session(self):
        return Session(
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        )

    async def _perform_ses_action(self, action_callback):
        session = await self._ses_session()
        async with session.client(
            "ses", endpoint_url=settings.ENDPOINT_URL, region_name=self.region_name
        ) as ses:
            try:
                return await action_callback(ses)
            except Exception as e:
                logger.error(f"SES action error: {e} ({type(e)})")
                raise HTTPException(
                    status_code=500, detail="Error interacting with SES"
                )

    async def send_email(self, subject, body, sender, recipient):
        async def send_email_action(ses):
            return await ses.send_email(
                Source=sender,
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}},
                },
            )

        return await self._perform_ses_action(send_email_action)

    async def verify_email(self, email):
        async def verify_email_action(ses):
            return await ses.verify_email_identity(
                EmailAddress=email,
            )

        return await self._perform_ses_action(verify_email_action)
