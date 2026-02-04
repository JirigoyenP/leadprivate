from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HubSpotAuthURL(BaseModel):
    auth_url: str


class HubSpotContact(BaseModel):
    id: str
    email: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email_verification_status: Optional[str] = None
    email_verification_date: Optional[datetime] = None


class HubSpotContactList(BaseModel):
    contacts: list[HubSpotContact]
    total: int
    has_more: bool
    next_cursor: Optional[str] = None


class ContactToVerify(BaseModel):
    id: str
    email: str


class HubSpotSyncRequest(BaseModel):
    contacts: Optional[list[ContactToVerify]] = None  # If None, sync all unverified
    force_reverify: bool = False


class HubSpotVerifyAndEnrichRequest(BaseModel):
    contacts: Optional[list[ContactToVerify]] = None  # If None, process all unverified
    force_reverify: bool = False
    enrich_valid_only: bool = True  # Only enrich emails that pass verification


class HubSpotVerifyAndEnrichResponse(BaseModel):
    batch_id: int
    status: str
    contacts_queued: int
    message: str
    will_enrich: bool  # Whether Apollo enrichment will run after verification


class HubSpotSyncResponse(BaseModel):
    batch_id: int
    status: str
    contacts_queued: int
    message: str


class HubSpotConnectionStatus(BaseModel):
    connected: bool
    portal_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class HubSpotDeleteRequest(BaseModel):
    contact_ids: list[str]


class HubSpotDeleteResponse(BaseModel):
    deleted_count: int
    failed_count: int
    deleted: list[str]
    failed: list[dict]
