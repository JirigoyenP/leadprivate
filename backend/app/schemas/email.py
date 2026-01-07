from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class EmailVerifyRequest(BaseModel):
    email: EmailStr


class EmailVerifyResponse(BaseModel):
    email: str
    status: str  # valid, invalid, catch-all, unknown, spamtrap, abuse, do_not_mail
    sub_status: Optional[str] = None
    score: Optional[int] = None
    free_email: Optional[bool] = None
    did_you_mean: Optional[str] = None
    domain: Optional[str] = None
    domain_age_days: Optional[int] = None
    smtp_provider: Optional[str] = None
    mx_found: Optional[bool] = None
    mx_record: Optional[str] = None
    verified_at: datetime

    class Config:
        from_attributes = True


class BatchVerifyRequest(BaseModel):
    emails: list[EmailStr]


class BatchVerifyResponse(BaseModel):
    results: list[EmailVerifyResponse]
    total: int
    valid_count: int
    invalid_count: int
    unknown_count: int
