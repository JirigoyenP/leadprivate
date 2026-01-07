from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from app.database import Base


class ContactEnrichment(Base):
    """Stores Apollo.io enrichment results for contacts."""

    __tablename__ = "contact_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    enriched = Column(Boolean, default=False)

    # Personal info
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    full_name = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    headline = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    phone_numbers = Column(JSON, nullable=True)  # List of phone numbers
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)

    # Employment info
    employment_history = Column(JSON, nullable=True)  # List of employment records
    seniority = Column(String(100), nullable=True)
    departments = Column(JSON, nullable=True)  # List of departments

    # Company info
    company_name = Column(String(500), nullable=True)
    company_domain = Column(String(255), nullable=True)
    company_industry = Column(String(255), nullable=True)
    company_size = Column(Integer, nullable=True)
    company_linkedin_url = Column(String(500), nullable=True)
    company_phone = Column(String(100), nullable=True)
    company_founded_year = Column(Integer, nullable=True)
    company_location = Column(String(500), nullable=True)

    # Metadata
    apollo_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    # Batch reference
    batch_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_contact_enrichments_email_created", "email", "created_at"),
    )
