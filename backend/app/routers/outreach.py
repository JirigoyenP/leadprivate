"""
Outreach router - Instantly.ai integration for pushing leads to campaigns.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.lead import Lead
from app.models.outreach import InstantlyConnection, OutreachCampaign, OutreachLog
from app.schemas.outreach import (
    ConnectRequest,
    ConnectResponse,
    CampaignResponse,
    PushRequest,
    PushResponse,
    OutreachLogResponse,
    OutreachLogList,
    ExportFormatRequest,
)
from app.services.instantly import InstantlyService, InstantlyError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


def _get_instantly_service(db: Session) -> InstantlyService:
    """Get an InstantlyService instance using the stored API key."""
    connection = (
        db.query(InstantlyConnection)
        .filter(InstantlyConnection.is_active == True)
        .order_by(desc(InstantlyConnection.created_at))
        .first()
    )
    if not connection:
        raise HTTPException(status_code=400, detail="Instantly.ai not connected. Add your API key first.")
    return InstantlyService(api_key=connection.api_key)


@router.post("/connect", response_model=ConnectResponse)
async def connect(request: ConnectRequest, db: Session = Depends(get_db)):
    """Save API key and verify connection to Instantly.ai."""
    service = InstantlyService(api_key=request.api_key)
    result = await service.test_connection()

    if not result.get("connected"):
        return ConnectResponse(connected=False, error=result.get("error", "Connection failed"))

    # Deactivate old connections
    db.query(InstantlyConnection).filter(InstantlyConnection.is_active == True).update(
        {"is_active": False}
    )

    # Save new connection
    connection = InstantlyConnection(
        api_key=request.api_key,
        is_active=True,
    )
    db.add(connection)
    db.commit()

    return ConnectResponse(connected=True)


@router.get("/status")
async def connection_status(db: Session = Depends(get_db)):
    """Check if Instantly.ai is connected."""
    connection = (
        db.query(InstantlyConnection)
        .filter(InstantlyConnection.is_active == True)
        .first()
    )
    if not connection:
        return {"connected": False}

    service = InstantlyService(api_key=connection.api_key)
    result = await service.test_connection()
    return {
        "connected": result.get("connected", False),
        "workspace_name": connection.workspace_name,
        "connected_at": connection.created_at.isoformat() if connection.created_at else None,
    }


@router.delete("/disconnect")
async def disconnect(db: Session = Depends(get_db)):
    """Disconnect from Instantly.ai."""
    db.query(InstantlyConnection).filter(InstantlyConnection.is_active == True).update(
        {"is_active": False}
    )
    db.commit()
    return {"disconnected": True}


@router.get("/campaigns")
async def list_campaigns(db: Session = Depends(get_db)):
    """List campaigns from Instantly.ai."""
    service = _get_instantly_service(db)

    try:
        campaigns = await service.list_campaigns()
    except InstantlyError as e:
        raise HTTPException(status_code=502, detail=str(e))

    result = []
    for camp in campaigns:
        camp_id = camp.get("id", camp.get("campaign_id", ""))
        camp_name = camp.get("name", camp.get("campaign_name", ""))
        camp_status = camp.get("status", "")

        result.append({
            "id": camp_id,
            "name": camp_name,
            "status": camp_status,
        })

        # Cache campaign locally
        existing = db.query(OutreachCampaign).filter(
            OutreachCampaign.instantly_campaign_id == camp_id
        ).first()
        if not existing:
            db.add(OutreachCampaign(
                instantly_campaign_id=camp_id,
                name=camp_name,
                status=camp_status,
            ))
        else:
            existing.name = camp_name
            existing.status = camp_status

    db.commit()
    return {"campaigns": result}


@router.post("/push", response_model=PushResponse)
async def push_leads(request: PushRequest, db: Session = Depends(get_db)):
    """Push leads to an Instantly.ai campaign."""
    service = _get_instantly_service(db)

    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found with given IDs")

    # Prepare lead data for Instantly
    lead_data_list = []
    for lead in leads:
        lead_data_list.append({
            "email": lead.email,
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "company_name": lead.company_name,
            "title": lead.title,
            "phone": lead.phone,
            "linkedin_url": lead.linkedin_url,
        })

    pushed = 0
    failed = 0

    try:
        result = await service.push_leads_to_campaign(request.campaign_id, lead_data_list)

        # Create outreach logs
        for lead in leads:
            variables = {
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company_name": lead.company_name,
                "title": lead.title,
            }
            log = OutreachLog(
                lead_id=lead.id,
                campaign_id=request.campaign_id,
                campaign_name=request.campaign_name,
                status="pushed",
                variables_sent=variables,
            )
            db.add(log)

            # Update lead outreach status
            lead.outreach_status = "pushed"
            pushed += 1

        db.commit()

    except InstantlyError as e:
        logger.error(f"Failed to push leads to Instantly: {e}")
        failed = len(leads)
        raise HTTPException(status_code=502, detail=str(e))

    return PushResponse(
        pushed=pushed,
        failed=failed,
        message=f"Successfully pushed {pushed} leads to campaign",
    )


@router.get("/logs", response_model=OutreachLogList)
async def get_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    campaign_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get outreach history logs."""
    query = db.query(OutreachLog)

    if campaign_id:
        query = query.filter(OutreachLog.campaign_id == campaign_id)

    total = query.count()
    logs = query.order_by(desc(OutreachLog.created_at)).offset(offset).limit(limit).all()

    return OutreachLogList(
        logs=[OutreachLogResponse.model_validate(log) for log in logs],
        total=total,
    )


@router.post("/export")
async def smart_export(request: ExportFormatRequest, db: Session = Depends(get_db)):
    """Smart CSV export formatted for specific outreach tools."""
    query = db.query(Lead)

    if request.lead_ids:
        query = query.filter(Lead.id.in_(request.lead_ids))

    if request.filters:
        if request.filters.get("source"):
            query = query.filter(Lead.source == request.filters["source"])
        if request.filters.get("verification_status"):
            query = query.filter(Lead.verification_status == request.filters["verification_status"])
        if request.filters.get("score_min"):
            query = query.filter(Lead.lead_score >= request.filters["score_min"])

    leads = query.all()

    # Format presets
    if request.format == "instantly":
        columns = ["email", "first_name", "last_name", "company_name", "title", "phone", "linkedin_url"]
        headers = ["Email", "First Name", "Last Name", "Company Name", "Title", "Phone", "LinkedIn URL"]
    elif request.format == "lemlist":
        columns = ["email", "first_name", "last_name", "company_name", "linkedin_url"]
        headers = ["email", "firstName", "lastName", "companyName", "linkedinUrl"]
    else:
        columns = [
            "email", "first_name", "last_name", "full_name", "title", "phone",
            "linkedin_url", "company_name", "company_domain", "company_industry",
            "company_size", "seniority", "verification_status", "lead_score",
        ]
        headers = columns

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for lead in leads:
        row = [getattr(lead, col, "") or "" for col in columns]
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=leads_{request.format}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )
