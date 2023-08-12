import logging

from fastapi import APIRouter

from logs.logs import configure_logger
from src.settings import Settings

router = APIRouter()

settings = Settings()
logger = logging.getLogger(__name__)
logger_path = settings.model_dump().get("CONFIG_LOGGER_PATH")


@router.get("/healthcheck/")
async def health_check():
    configure_logger(logger_path)
    logger.info("Health check endpoint accessed")
    return {"result": "You've successfully checked your health!"}
