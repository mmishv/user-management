from fastapi import FastAPI

from logs.logs import configure_logger
from src.database import create_async_session, get_db, get_redis
from src.other.router import router as other_router

app = FastAPI()
logger = configure_logger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    async with create_async_session() as db_session:
        app.state.db_session = db_session

        async with get_db() as db_connection:
            app.state.db = db_connection

        async with get_redis() as redis:
            app.state.redis = redis
    logger.info("Startup completed.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    await app.state.db_session.close()
    await app.state.db.close()
    await app.state.redis.close()
    logger.info("Shutdown completed.")


app.include_router(other_router)
