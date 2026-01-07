from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BatchJobCreate(BaseModel):
    filename: str
    total_emails: int = 0
    source: str = "csv"


class BatchJobStatus(BaseModel):
    id: int
    filename: str
    status: str
    total_emails: int
    processed_emails: int
    valid_count: int
    invalid_count: int
    unknown_count: int
    progress_percent: float
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchJobResponse(BaseModel):
    id: int
    filename: str
    status: str
    message: str

    class Config:
        from_attributes = True
