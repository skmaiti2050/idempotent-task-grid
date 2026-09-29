import os
import redis.asyncio as redis

class RedisClient:
    def __init__(self):
        self.redis = None

    async def connect(self):
        # Default to local redis if REDIS_URL not set
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.from_url(url, decode_responses=True, protocol=2)

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

# Singleton instance
redis_client = RedisClient()
