from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LinkedInKeywordBase(BaseModel):
    keyword: str


class LinkedInKeywordCreate(LinkedInKeywordBase):
    pass


class LinkedInKeywordResponse(LinkedInKeywordBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LinkedInKeywordList(BaseModel):
    keywords: list[LinkedInKeywordResponse]
    total: int


class LinkedInPostResponse(BaseModel):
    id: int
    author_name: Optional[str] = None
    author_profile_url: Optional[str] = None
    author_country: Optional[str] = None
    post_text: Optional[str] = None
    post_date: Optional[datetime] = None
    comments_count: int = 0
    keywords_matched: Optional[list[str]] = None
    scraped_at: datetime
    is_processed: bool = False

    class Config:
        from_attributes = True


class LinkedInPostList(BaseModel):
    posts: list[LinkedInPostResponse]
    total: int
    unprocessed_count: int


class LinkedInScrapeRequest(BaseModel):
    search_type: str = "feed"  # feed or search
    keywords: Optional[list[str]] = None  # Custom keywords (optional)
    max_scrolls: int = 10


class LinkedInScrapeJobResponse(BaseModel):
    id: int
    search_type: str
    status: str
    keywords_used: Optional[list[str]] = None
    posts_found: int
    posts_saved: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_scheduled: bool = False

    class Config:
        from_attributes = True


class LinkedInScrapeJobList(BaseModel):
    jobs: list[LinkedInScrapeJobResponse]
    total: int


class LinkedInProcessLeadsRequest(BaseModel):
    post_ids: Optional[list[int]] = None  # Specific posts to process (None = all unprocessed)
    enrich_with_apollo: bool = True


class LinkedInProcessLeadsResponse(BaseModel):
    batch_id: int
    status: str
    leads_queued: int
    message: str


class LinkedInScheduleRequest(BaseModel):
    enabled: bool
    schedule: str = "0 8 * * *"  # Cron format
    search_type: str = "feed"
    keywords: Optional[list[str]] = None


class LinkedInScheduleResponse(BaseModel):
    enabled: bool
    schedule: str
    next_run: Optional[datetime] = None
