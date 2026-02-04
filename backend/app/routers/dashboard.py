"""
Dashboard router - aggregate stats, activity timeline, credit balances.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc

from app.database import get_db
from app.models.email import EmailVerification
from app.models.enrichment import ContactEnrichment
from app.models.batch import BatchJob
from app.models.hubspot_sync import HubSpotSyncLog
from app.models.linkedin import LinkedInScrapeJob
from app.services.zerobounce import get_zerobounce_service
from app.services.apollo import get_apollo_service, ApolloError

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Aggregate counts: leads, verified, enriched, verification breakdown, enrichment coverage."""
    total_verified = db.query(func.count(EmailVerification.id)).scalar() or 0

    # Verification breakdown
    verification_breakdown = dict(
        db.query(
            EmailVerification.status,
            func.count(EmailVerification.id),
        )
        .group_by(EmailVerification.status)
        .all()
    )

    # Unique emails verified
    unique_verified = db.query(func.count(func.distinct(EmailVerification.email))).scalar() or 0

    # Enrichment stats
    total_enrichments = db.query(func.count(ContactEnrichment.id)).scalar() or 0
    enriched_count = (
        db.query(func.count(ContactEnrichment.id))
        .filter(ContactEnrichment.enriched == True)
        .scalar()
        or 0
    )
    unique_enriched = (
        db.query(func.count(func.distinct(ContactEnrichment.email)))
        .filter(ContactEnrichment.enriched == True)
        .scalar()
        or 0
    )

    # Enrichment coverage: how many have phone, linkedin, company, title
    coverage = {}
    if total_enrichments > 0:
        coverage["phone"] = (
            db.query(func.count(ContactEnrichment.id))
            .filter(ContactEnrichment.phone_numbers.isnot(None))
            .scalar()
            or 0
        )
        coverage["linkedin"] = (
            db.query(func.count(ContactEnrichment.id))
            .filter(ContactEnrichment.linkedin_url.isnot(None))
            .scalar()
            or 0
        )
        coverage["company"] = (
            db.query(func.count(ContactEnrichment.id))
            .filter(ContactEnrichment.company_name.isnot(None))
            .scalar()
            or 0
        )
        coverage["title"] = (
            db.query(func.count(ContactEnrichment.id))
            .filter(ContactEnrichment.title.isnot(None))
            .scalar()
            or 0
        )
    else:
        coverage = {"phone": 0, "linkedin": 0, "company": 0, "title": 0}

    # Batch stats
    total_batches = db.query(func.count(BatchJob.id)).scalar() or 0
    completed_batches = (
        db.query(func.count(BatchJob.id))
        .filter(BatchJob.status == "completed")
        .scalar()
        or 0
    )

    return {
        "total_verified": total_verified,
        "unique_verified": unique_verified,
        "verification_breakdown": verification_breakdown,
        "total_enrichments": total_enrichments,
        "enriched_count": enriched_count,
        "unique_enriched": unique_enriched,
        "enrichment_coverage": coverage,
        "total_batches": total_batches,
        "completed_batches": completed_batches,
    }


@router.get("/activity")
async def get_activity(limit: int = 20, db: Session = Depends(get_db)):
    """Recent BatchJobs + HubSpotSyncLogs + LinkedInScrapeJobs merged into a timeline."""
    activities = []

    # Recent batch jobs
    batches = (
        db.query(BatchJob)
        .order_by(desc(BatchJob.created_at))
        .limit(limit)
        .all()
    )
    for b in batches:
        activities.append({
            "type": "batch",
            "id": b.id,
            "title": f"Batch: {b.filename}",
            "status": b.status,
            "detail": f"{b.processed_emails}/{b.total_emails} emails processed",
            "source": b.source,
            "timestamp": b.created_at.isoformat() if b.created_at else None,
        })

    # Recent HubSpot sync logs
    syncs = (
        db.query(HubSpotSyncLog)
        .order_by(desc(HubSpotSyncLog.created_at))
        .limit(limit)
        .all()
    )
    for s in syncs:
        activities.append({
            "type": "hubspot_sync",
            "id": s.id,
            "title": f"HubSpot {s.sync_type}",
            "status": s.status,
            "detail": f"{s.contacts_processed} contacts processed, {s.contacts_updated} updated",
            "timestamp": s.created_at.isoformat() if s.created_at else None,
        })

    # Recent LinkedIn scrape jobs
    scrapes = (
        db.query(LinkedInScrapeJob)
        .order_by(desc(LinkedInScrapeJob.created_at))
        .limit(limit)
        .all()
    )
    for sc in scrapes:
        activities.append({
            "type": "linkedin_scrape",
            "id": sc.id,
            "title": f"LinkedIn {sc.search_type} scrape",
            "status": sc.status,
            "detail": f"{sc.posts_found} posts found, {sc.posts_saved} saved",
            "timestamp": sc.created_at.isoformat() if sc.created_at else None,
        })

    # Sort by timestamp descending, handle None
    activities.sort(key=lambda x: x["timestamp"] or "", reverse=True)

    return {"activities": activities[:limit]}


@router.get("/credits")
async def get_credits():
    """ZeroBounce + Apollo credit balances."""
    credits = {}

    # ZeroBounce credits
    try:
        zb_service = get_zerobounce_service()
        zb_credits = await zb_service.get_credits()
        credits["zerobounce"] = {"credits": zb_credits, "status": "connected"}
    except Exception as e:
        credits["zerobounce"] = {"credits": None, "status": "error", "error": str(e)}

    # Apollo credits
    try:
        apollo_service = get_apollo_service()
        apollo_credits = await apollo_service.get_credits()
        credits["apollo"] = apollo_credits
    except Exception as e:
        credits["apollo"] = {"credits": None, "status": "error", "error": str(e)}

    return credits
