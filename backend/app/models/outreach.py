"""
Outreach models - Instantly.ai integration for campaign management.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class InstantlyConnection(Base):
    """Stores Instantly.ai API key and connection status."""

    __tablename__ = "instantly_connections"

    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(Text, nullable=False)
    workspace_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OutreachCampaign(Base):
    """Cached campaign metadata from Instantly."""

    __tablename__ = "outreach_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    instantly_campaign_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)  # active, paused, completed, draft

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OutreachLog(Base):
    """Per-lead push tracking to Instantly campaigns."""

    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    campaign_id = Column(String(255), nullable=False)  # Instantly campaign ID
    campaign_name = Column(String(500), nullable=True)
    status = Column(String(50), default="pushed")  # pushed, contacted, replied, bounced
    instantly_lead_id = Column(String(255), nullable=True)

    # Personalization fields sent
    variables_sent = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
