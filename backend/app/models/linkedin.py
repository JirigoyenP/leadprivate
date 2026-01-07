from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from app.database import Base


class LinkedInKeyword(Base):
    """Keywords used for LinkedIn post searching."""

    __tablename__ = "linkedin_keywords"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LinkedInPost(Base):
    """LinkedIn posts scraped by the bot."""

    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, index=True)

    # Author info
    author_name = Column(String(500), nullable=True)
    author_profile_url = Column(String(1000), nullable=True)
    author_country = Column(String(255), nullable=True)

    # Post content
    post_text = Column(Text, nullable=True)
    post_date = Column(DateTime(timezone=True), nullable=True)
    comments_count = Column(Integer, default=0)

    # Keywords that matched this post
    keywords_matched = Column(JSON, nullable=True)  # List of keyword IDs

    # Scraping metadata
    scrape_batch_id = Column(Integer, ForeignKey("linkedin_scrape_jobs.id"), nullable=True, index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    # Lead processing status
    is_processed = Column(Boolean, default=False)  # Has been sent to enrichment
    enrichment_batch_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=True)

    __table_args__ = (
        Index("ix_linkedin_posts_author_scraped", "author_profile_url", "scraped_at"),
    )


class LinkedInScrapeJob(Base):
    """Tracks LinkedIn scraping jobs."""

    __tablename__ = "linkedin_scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Job configuration
    keywords_used = Column(JSON, nullable=True)  # List of keywords searched
    search_type = Column(String(50), default="feed")  # feed, search, profile

    # Status
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    posts_found = Column(Integer, default=0)
    posts_saved = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Scheduling
    is_scheduled = Column(Boolean, default=False)  # Was this a scheduled run?
