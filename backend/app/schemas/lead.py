"""Pydantic schemas for lead endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class LeadResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[int] = None
    company_location: Optional[str] = None
    verification_status: Optional[str] = None
    enriched: bool = False
    seniority: Optional[str] = None
    lead_score: int = 0
    score_breakdown: Optional[dict] = None
    source: Optional[str] = None
    outreach_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadDetailResponse(LeadResponse):
    verification_sub_status: Optional[str] = None
    verification_score: Optional[int] = None
    headline: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    departments: Optional[list] = None
    phone_numbers: Optional[list] = None
    latest_verification_id: Optional[int] = None
    latest_enrichment_id: Optional[int] = None


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BulkActionRequest(BaseModel):
    lead_ids: list[int]
    action: str  # verify, enrich, score, export, push_outreach


class BulkActionResponse(BaseModel):
    action: str
    affected: int
    batch_id: Optional[int] = None
    message: str


class ProcessLeadsRequest(BaseModel):
    lead_ids: Optional[list[int]] = None  # None = all unprocessed


class ProcessLeadsResponse(BaseModel):
    batch_id: int
    status: str
    leads_queued: int
    message: str


class ExportRequest(BaseModel):
    lead_ids: Optional[list[int]] = None
    columns: Optional[list[str]] = None
    filters: Optional[dict] = None


class ScoringConfigResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    config: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScoringConfigUpdate(BaseModel):
    config: dict
