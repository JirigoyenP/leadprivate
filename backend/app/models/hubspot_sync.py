from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base


class HubSpotConnection(Base):
    __tablename__ = "hubspot_connections"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    portal_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class HubSpotSyncLog(Base):
    __tablename__ = "hubspot_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False)  # fetch, verify, sync_results
    status = Column(String(50), nullable=False)  # pending, in_progress, completed, failed
    contacts_processed = Column(Integer, default=0)
    contacts_updated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Reference to batch job if applicable
    batch_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
