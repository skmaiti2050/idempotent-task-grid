import time
from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config.redis_client import redis_client

security = HTTPBearer()

def get_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Extracts the bearer token from the Authorization header."""
    return credentials.credentials

async def verify_rate_limit(token: str = Depends(get_token)) -> str:
    """
    Checks if the token has exceeded the maximum allowed requests per minute.
    Allows a maximum of 5 requests per minute per token.
    """
    redis = redis_client.redis
    if not redis:
        # Fallback if redis is not connected (e.g., in unit tests)
        return token
        
    current_minute = int(time.time() // 60)
    key = f"rate_limit:{token}:{current_minute}"
    
    # Use a pipeline to ensure atomic increment and expiry
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    results = await pipe.execute()
    
    count = results[0]
    if count > 5:
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    return token

def get_idempotency_key(idempotency_key: str = Header(..., alias="Idempotency-Key")) -> str:
    """Extracts the Idempotency-Key from the request headers."""
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    return idempotency_key
