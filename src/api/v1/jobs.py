import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from src.schemas.job import JobSubmitRequest, JobSubmitResponse, JobStatusResponse
from src.api.dependencies import verify_rate_limit, get_idempotency_key
from src.services.job_service import process_job_background
from src.config.redis_client import redis_client

router = APIRouter()

@router.post("", response_model=JobSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_job(
    request: JobSubmitRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_rate_limit),
    idemp_key: str = Depends(get_idempotency_key),
):
    redis = redis_client.redis
    if not redis:
        raise HTTPException(status_code=500, detail="Redis connection failed")
        
    idemp_store_key = f"idemp:{token}:{idemp_key}"
    new_job_id = str(uuid.uuid4())
    
    # Try to set the idempotency key to the new job_id if it doesn't exist (with 24h expiry)
    is_new = await redis.set(idemp_store_key, new_job_id, nx=True, ex=86400)
    
    if is_new:
        # We are the first to make this request
        job_id = new_job_id
        
        # Initialize job state
        await redis.hset(f"job:{job_id}", mapping={
            "status": "pending",
            "result": ""
        })
        await redis.expire(f"job:{job_id}", 86400) # Expire job state in 24 hours
        
        # Enqueue background task
        background_tasks.add_task(process_job_background, job_id, request.payload)
        
        return JobSubmitResponse(job_id=job_id, status="pending")
    else:
        # Duplicate request, retrieve existing job_id and status
        job_id = await redis.get(idemp_store_key)
        job_data = await redis.hgetall(f"job:{job_id}")
        
        if not job_data:
            # Fallback if job data expired but idempotency key exists (rare edge case)
            return JobSubmitResponse(job_id=job_id, status="pending")
            
        return JobSubmitResponse(job_id=job_id, status=job_data.get("status", "pending"))

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    redis = redis_client.redis
    if not redis:
        raise HTTPException(status_code=500, detail="Redis connection failed")
        
    job_data = await redis.hgetall(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
        
    result = job_data.get("result")
    # If result is empty string, convert to None
    if not result:
        result = None
        
    return JobStatusResponse(
        job_id=job_id,
        status=job_data.get("status"),
        result=result
    )
