from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.v1.router import api_router
from src.config.redis_client import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to Redis
    await redis_client.connect()
    yield
    # Shutdown: close Redis connection
    await redis_client.disconnect()

app = FastAPI(
    title="Idempotent Task Grid",
    description="A simple API for asynchronous computation jobs.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
