"""
Leads router - central hub for all lead operations.
Paginated listing, filtering, bulk actions, export, scoring config.
"""

import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_

from app.database import get_db
from app.models.lead import Lead, ScoringConfig
from app.schemas.lead import (
    LeadResponse,
    LeadDetailResponse,
    LeadListResponse,
    BulkActionRequest,
    BulkActionResponse,
    ProcessLeadsRequest,
    ProcessLeadsResponse,
    ScoringConfigResponse,
    ScoringConfigUpdate,
)
from app.services.scoring import rescore_all_leads, DEFAULT_CONFIG
from app.services.lead_manager import backfill_leads

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    source: Optional[str] = None,
    verification_status: Optional[str] = None,
    outreach_status: Optional[str] = None,
    score_min: Optional[int] = Query(None, ge=0, le=100),
    score_max: Optional[int] = Query(None, ge=0, le=100),
    enriched: Optional[bool] = None,
    sort_by: str = Query("created_at", regex="^(created_at|lead_score|email|company_name|verification_status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Paginated, filterable, sortable lead listing."""
    query = db.query(Lead)

    # Filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Lead.email.ilike(search_term),
                Lead.full_name.ilike(search_term),
                Lead.first_name.ilike(search_term),
                Lead.last_name.ilike(search_term),
                Lead.company_name.ilike(search_term),
                Lead.title.ilike(search_term),
            )
        )

    if source:
        query = query.filter(Lead.source == source)

    if verification_status:
        query = query.filter(Lead.verification_status == verification_status)

    if outreach_status:
        query = query.filter(Lead.outreach_status == outreach_status)

    if score_min is not None:
        query = query.filter(Lead.lead_score >= score_min)

    if score_max is not None:
        query = query.filter(Lead.lead_score <= score_max)

    if enriched is not None:
        query = query.filter(Lead.enriched == enriched)

    # Count total
    total = query.count()

    # Sort
    sort_column = getattr(Lead, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Paginate
    offset = (page - 1) * page_size
    leads = query.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size

    return LeadListResponse(
        leads=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/pipeline-summary")
async def pipeline_summary(db: Session = Depends(get_db)):
    """Counts at each pipeline stage."""
    total = db.query(func.count(Lead.id)).scalar() or 0
    verified = (
        db.query(func.count(Lead.id))
        .filter(Lead.verification_status.isnot(None))
        .scalar() or 0
    )
    valid = (
        db.query(func.count(Lead.id))
        .filter(Lead.verification_status == "valid")
        .scalar() or 0
    )
    enriched = (
        db.query(func.count(Lead.id))
        .filter(Lead.enriched == True)
        .scalar() or 0
    )
    scored = (
        db.query(func.count(Lead.id))
        .filter(Lead.lead_score > 0)
        .scalar() or 0
    )
    outreach = (
        db.query(func.count(Lead.id))
        .filter(Lead.outreach_status.isnot(None))
        .scalar() or 0
    )
    avg_score = db.query(func.avg(Lead.lead_score)).scalar() or 0

    return {
        "imported": total,
        "verified": verified,
        "valid": valid,
        "enriched": enriched,
        "scored": scored,
        "outreach": outreach,
        "avg_score": round(avg_score, 1),
    }


@router.get("/export")
async def export_leads(
    lead_ids: Optional[str] = Query(None, description="Comma-separated lead IDs"),
    columns: Optional[str] = Query(None, description="Comma-separated column names"),
    source: Optional[str] = None,
    verification_status: Optional[str] = None,
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """CSV export with column selection."""
    query = db.query(Lead)

    if lead_ids:
        ids = [int(x.strip()) for x in lead_ids.split(",") if x.strip()]
        query = query.filter(Lead.id.in_(ids))

    if source:
        query = query.filter(Lead.source == source)
    if verification_status:
        query = query.filter(Lead.verification_status == verification_status)
    if score_min is not None:
        query = query.filter(Lead.lead_score >= score_min)
    if score_max is not None:
        query = query.filter(Lead.lead_score <= score_max)

    leads = query.all()

    default_columns = [
        "email", "first_name", "last_name", "full_name", "title", "phone",
        "linkedin_url", "company_name", "company_domain", "company_industry",
        "company_size", "verification_status", "seniority", "lead_score",
        "source", "outreach_status",
    ]

    if columns:
        selected = [c.strip() for c in columns.split(",")]
    else:
        selected = default_columns

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(selected)

    for lead in leads:
        row = [getattr(lead, col, "") for col in selected]
        writer.writerow(row)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=leads_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"},
    )


@router.get("/scoring-config", response_model=ScoringConfigResponse)
async def get_scoring_config(db: Session = Depends(get_db)):
    """Get current active scoring configuration."""
    config = (
        db.query(ScoringConfig)
        .filter(ScoringConfig.is_active == True)
        .order_by(desc(ScoringConfig.updated_at))
        .first()
    )
    if not config:
        # Create default
        config = ScoringConfig(name="default", is_active=True, config=DEFAULT_CONFIG)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/scoring-config", response_model=ScoringConfigResponse)
async def update_scoring_config(
    update: ScoringConfigUpdate,
    db: Session = Depends(get_db),
):
    """Update scoring configuration."""
    config = (
        db.query(ScoringConfig)
        .filter(ScoringConfig.is_active == True)
        .order_by(desc(ScoringConfig.updated_at))
        .first()
    )
    if not config:
        config = ScoringConfig(name="default", is_active=True, config=update.config)
        db.add(config)
    else:
        config.config = update.config

    db.commit()
    db.refresh(config)
    return config


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get lead detail with score breakdown."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_action(request: BulkActionRequest, db: Session = Depends(get_db)):
    """Perform bulk action on selected leads."""
    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()

    if not leads:
        raise HTTPException(status_code=404, detail="No leads found with given IDs")

    if request.action == "score":
        from app.services.scoring import score_and_update_lead, get_active_config
        config = get_active_config(db)
        for lead in leads:
            score_and_update_lead(lead, db, config)
        db.commit()
        return BulkActionResponse(
            action="score",
            affected=len(leads),
            message=f"Rescored {len(leads)} leads",
        )

    elif request.action == "verify":
        # Queue verification for leads that haven't been verified
        from app.models.batch import BatchJob
        batch = BatchJob(
            filename="bulk_verify",
            status="pending",
            total_emails=len(leads),
            source="leads",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        contact_data = [{"email": lead.email, "id": str(lead.id)} for lead in leads]

        from app.tasks.verification import process_hubspot_contacts
        process_hubspot_contacts.delay(batch.id, contact_data)

        return BulkActionResponse(
            action="verify",
            affected=len(leads),
            batch_id=batch.id,
            message=f"Queued {len(leads)} leads for verification",
        )

    elif request.action == "enrich":
        from app.models.batch import BatchJob
        batch = BatchJob(
            filename="bulk_enrich",
            status="pending",
            total_emails=len(leads),
            source="leads",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        contact_data = [{"email": lead.email} for lead in leads]

        from app.tasks.enrichment import enrich_contacts_with_apollo
        enrich_contacts_with_apollo.delay(batch.id, contact_data)

        return BulkActionResponse(
            action="enrich",
            affected=len(leads),
            batch_id=batch.id,
            message=f"Queued {len(leads)} leads for enrichment",
        )

    elif request.action == "export":
        # Export is handled by the GET /export endpoint
        return BulkActionResponse(
            action="export",
            affected=len(leads),
            message="Use GET /api/leads/export with lead_ids parameter",
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")


@router.post("/process", response_model=ProcessLeadsResponse)
async def process_leads(request: ProcessLeadsRequest, db: Session = Depends(get_db)):
    """One-click verify->enrich->score pipeline."""
    from app.models.batch import BatchJob

    if request.lead_ids:
        leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    else:
        # All leads not yet fully processed
        leads = (
            db.query(Lead)
            .filter(
                or_(
                    Lead.verification_status.is_(None),
                    Lead.enriched == False,
                )
            )
            .all()
        )

    if not leads:
        raise HTTPException(status_code=400, detail="No leads to process")

    batch = BatchJob(
        filename="pipeline_process",
        status="pending",
        total_emails=len(leads),
        source="leads",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    contact_data = [{"email": lead.email, "id": str(lead.id)} for lead in leads]

    from app.tasks.pipeline import run_lead_pipeline
    run_lead_pipeline.delay(batch.id, contact_data)

    return ProcessLeadsResponse(
        batch_id=batch.id,
        status="queued",
        leads_queued=len(leads),
        message=f"Pipeline started for {len(leads)} leads",
    )


@router.post("/backfill")
async def backfill(db: Session = Depends(get_db)):
    """Populate leads from existing verification and enrichment data."""
    result = backfill_leads(db)
    return result


@router.post("/rescore")
async def rescore(db: Session = Depends(get_db)):
    """Recalculate all lead scores."""
    count = rescore_all_leads(db)
    return {"rescored": count, "message": f"Rescored {count} leads"}
