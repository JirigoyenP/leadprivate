"""
Lead model - the unified source of truth for all leads in the system.
ScoringConfig - configurable scoring weights and criteria.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Float,
    ForeignKey, Index, JSON, UniqueConstraint,
)
from sqlalchemy.sql import func
from app.database import Base


class Lead(Base):
    """
    Unified lead record. Denormalized from EmailVerification and ContactEnrichment
    for fast querying. Original tables remain as audit trail.
    """

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    email = Column(String(255), nullable=False, unique=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    full_name = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    phone = Column(String(100), nullable=True)
    linkedin_url = Column(String(500), nullable=True)

    # Company fields
    company_name = Column(String(500), nullable=True)
    company_domain = Column(String(255), nullable=True)
    company_industry = Column(String(255), nullable=True)
    company_size = Column(Integer, nullable=True)
    company_location = Column(String(500), nullable=True)

    # Verification data
    verification_status = Column(String(50), nullable=True)  # valid, invalid, catch-all, unknown
    verification_sub_status = Column(String(100), nullable=True)
    verification_score = Column(Integer, nullable=True)  # ZeroBounce AI score

    # Enrichment data
    enriched = Column(Boolean, default=False)
    seniority = Column(String(100), nullable=True)  # C-Level, VP, Director, Manager, etc.
    headline = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    departments = Column(JSON, nullable=True)
    phone_numbers = Column(JSON, nullable=True)

    # Lead scoring
    lead_score = Column(Integer, default=0)  # 0-100
    score_breakdown = Column(JSON, nullable=True)  # { email_quality: 25, seniority: 20, ... }

    # Source tracking
    source = Column(String(50), default="csv")  # csv, hubspot, linkedin, apollo

    # Outreach status
    outreach_status = Column(String(50), nullable=True)  # null, pushed, contacted, replied, bounced

    # Foreign keys to audit trail
    latest_verification_id = Column(Integer, ForeignKey("email_verifications.id"), nullable=True)
    latest_enrichment_id = Column(Integer, ForeignKey("contact_enrichments.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_leads_score", "lead_score"),
        Index("ix_leads_source", "source"),
        Index("ix_leads_verification_status", "verification_status"),
        Index("ix_leads_outreach_status", "outreach_status"),
        Index("ix_leads_created_at", "created_at"),
    )


class ScoringConfig(Base):
    """Configurable scoring weights and criteria."""

    __tablename__ = "scoring_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, default="default")
    is_active = Column(Boolean, default=True)

    # Weights and criteria stored as JSON for flexibility
    config = Column(JSON, nullable=False, default=lambda: {
        "weights": {
            "email_quality": 25,
            "seniority": 25,
            "company_fit": 25,
            "data_completeness": 25,
        },
        "seniority_scores": {
            "c_suite": 25,
            "vp": 20,
            "director": 15,
            "manager": 10,
            "other": 5,
        },
        "ideal_company_size": {
            "min": 50,
            "max": 5000,
        },
        "target_industries": [],
    })

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
