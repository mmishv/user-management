from fastapi import APIRouter

from logs.logs import configure_logger

router = APIRouter()
logger = configure_logger(__name__)


@router.get("/healthcheck/")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"result": "You've successfully checked your health!"}
