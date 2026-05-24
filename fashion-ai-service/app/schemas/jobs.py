from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class JobCreateResponse(BaseModel):
    """
    Pydantic schema representing the immediate response after launching an async job.
    """
    job_id: UUID
    status: str

class JobStatusResponse(BaseModel):
    """
    Pydantic schema representing the detailed status of a background job.
    """
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    job_type: str
    status: str
    progress: int
    error_message: Optional[str] = None
    result_reference: Optional[Any] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
