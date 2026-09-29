import asyncio
import hashlib
from src.config.redis_client import redis_client

async def process_job_background(job_id: str, payload: str):
    """
    Simulates a heavy compute task by sleeping for 7 seconds,
    computing the SHA-256 hash of the payload, and updating the
    job status in Redis.
    """
    # 1. Sleep for exactly 7 seconds
    await asyncio.sleep(7)
    
    # 2. Compute the SHA-256 hash
    result = hashlib.sha256(payload.encode()).hexdigest()
    
    # 3. Update job status to 'completed' with the hash as the result
    redis = redis_client.redis
    if redis:
        await redis.hset(f"job:{job_id}", mapping={
            "status": "completed",
            "result": result
        })
