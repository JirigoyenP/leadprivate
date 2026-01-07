from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    total_emails = Column(Integer, default=0)
    processed_emails = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    invalid_count = Column(Integer, default=0)
    unknown_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # File paths
    input_file_path = Column(String(500), nullable=True)
    output_file_path = Column(String(500), nullable=True)

    # Source tracking
    source = Column(String(50), default="csv")  # csv, hubspot

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
