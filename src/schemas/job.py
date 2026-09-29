from pydantic import BaseModel, Field
from typing import Optional

class JobSubmitRequest(BaseModel):
    payload: str = Field(..., description="The string to be hashed")

class JobSubmitResponse(BaseModel):
    job_id: str
    status: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
