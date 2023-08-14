from fastapi import FastAPI

from src.other.router import router as other_router

app = FastAPI()

app.include_router(other_router)
