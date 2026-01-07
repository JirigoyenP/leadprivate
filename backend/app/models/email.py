from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # valid, invalid, catch-all, unknown, spamtrap, abuse, do_not_mail
    sub_status = Column(String(100), nullable=True)  # More detailed status from ZeroBounce
    score = Column(Integer, nullable=True)  # ZeroBounce AI score (0-100)
    free_email = Column(String(10), nullable=True)  # true/false
    did_you_mean = Column(String(255), nullable=True)  # Suggested correction
    domain = Column(String(255), nullable=True)
    domain_age_days = Column(Integer, nullable=True)
    smtp_provider = Column(String(255), nullable=True)
    mx_found = Column(String(10), nullable=True)  # true/false
    mx_record = Column(String(255), nullable=True)

    # Batch reference
    batch_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_email_verifications_email_created", "email", "created_at"),
    )
