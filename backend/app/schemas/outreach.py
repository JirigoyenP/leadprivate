"""Pydantic schemas for outreach endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ConnectRequest(BaseModel):
    api_key: str


class ConnectResponse(BaseModel):
    connected: bool
    workspace_name: Optional[str] = None
    error: Optional[str] = None


class CampaignResponse(BaseModel):
    id: str
    name: Optional[str] = None
    status: Optional[str] = None


class PushRequest(BaseModel):
    lead_ids: list[int]
    campaign_id: str
    campaign_name: Optional[str] = None


class PushResponse(BaseModel):
    pushed: int
    failed: int
    message: str


class OutreachLogResponse(BaseModel):
    id: int
    lead_id: int
    campaign_id: str
    campaign_name: Optional[str] = None
    status: str
    variables_sent: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OutreachLogList(BaseModel):
    logs: list[OutreachLogResponse]
    total: int


class ExportFormatRequest(BaseModel):
    lead_ids: Optional[list[int]] = None
    format: str = "instantly"  # instantly, lemlist, general
    filters: Optional[dict] = None
