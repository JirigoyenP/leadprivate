"""
One-Click Pipeline router: Apollo Search → ZeroBounce Verify → HubSpot Push.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.batch import BatchJob
from app.schemas.pipeline import (
    ApolloSearchCriteria,
    OneClickPipelineRequest,
    OneClickPipelineResponse,
    PreviewSearchResponse,
    PipelineContact,
    PipelineResults,
    PipelineResultContact,
    HubSpotListsResponse,
    HubSpotListItem,
)
from app.services.apollo import get_apollo_service, ApolloError
from app.services.hubspot import get_hubspot_service, HubSpotError
from app.tasks.oneclick_pipeline import run_oneclick_pipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/hubspot-lists", response_model=HubSpotListsResponse)
async def get_hubspot_lists(db: Session = Depends(get_db)):
    """Return current HubSpot contact lists."""
    service = get_hubspot_service(db)
    try:
        raw_lists = await service.get_lists()
    except HubSpotError as e:
        raise HTTPException(status_code=502, detail=str(e))

    items = [
        HubSpotListItem(id=str(l["id"]), name=l["name"], size=int(l["size"]))
        for l in raw_lists
    ]
    return HubSpotListsResponse(lists=items)


@router.post("/preview-search", response_model=PreviewSearchResponse)
async def preview_search(criteria: ApolloSearchCriteria):
    """Preview Apollo search results before running the full pipeline."""
    apollo_service = get_apollo_service()

    try:
        result = await apollo_service.search_people(
            person_titles=criteria.person_titles or None,
            q_organization_domains=criteria.q_organization_domains or None,
            person_locations=criteria.person_locations or None,
            person_seniorities=criteria.person_seniorities or None,
            per_page=min(criteria.max_results, 10),
            page=1,
        )
    except ApolloError as e:
        raise HTTPException(status_code=502, detail=str(e))

    contacts = [
        PipelineContact(
            email=c["email"],
            first_name=c.get("first_name"),
            last_name=c.get("last_name"),
            title=c.get("title"),
            company_name=c.get("company_name"),
            company_domain=c.get("company_domain"),
            linkedin_url=c.get("linkedin_url"),
            seniority=c.get("seniority"),
        )
        for c in result.get("contacts", [])
    ]

    return PreviewSearchResponse(
        contacts=contacts,
        total_available=result.get("total_entries", 0),
        showing=len(contacts),
    )


@router.post("/oneclick", response_model=OneClickPipelineResponse)
async def start_oneclick_pipeline(
    request: OneClickPipelineRequest,
    db: Session = Depends(get_db),
):
    """Start the one-click pipeline: Apollo Search → ZeroBounce Verify → HubSpot Push."""
    criteria = request.search_criteria

    # Create batch job for tracking
    batch = BatchJob(
        filename=f"oneclick_pipeline_{criteria.person_titles or 'all'}",
        status="pending",
        source="apollo",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Kick off the Celery task
    run_oneclick_pipeline.delay(
        batch_id=batch.id,
        search_criteria=criteria.model_dump(),
    )

    return OneClickPipelineResponse(
        batch_id=batch.id,
        status="started",
        message="One-click pipeline started. Poll /api/progress/{batch_id} for updates.",
    )


@router.get("/{batch_id}/results", response_model=PipelineResults)
async def get_pipeline_results(batch_id: int, db: Session = Depends(get_db)):
    """Get final results of a completed pipeline run."""
    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get the Celery task result
    from app.tasks import celery_app

    result_data = None
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}

        # Check if task is still running
        for worker_tasks in active.values():
            for task in worker_tasks:
                task_args = task.get("args", [])
                if task_args and len(task_args) > 0 and task_args[0] == batch_id:
                    ar = celery_app.AsyncResult(task["id"])
                    if ar.ready():
                        result_data = ar.result
                    break

        # If not active, try to find completed result
        if result_data is None and batch.status == "completed":
            # Scan for completed tasks — use stored task_id if available
            # Fall back to batch data
            pass
    except Exception:
        pass

    contacts = []
    search_stats = {}
    verification_stats = {}
    hubspot_stats = {}

    if result_data and isinstance(result_data, dict):
        search_stats = result_data.get("search", {})
        verification_stats = result_data.get("verification", {})
        hubspot_stats = result_data.get("hubspot", {})
        for c in result_data.get("contacts", []):
            contacts.append(PipelineResultContact(
                email=c.get("email", ""),
                first_name=c.get("first_name"),
                last_name=c.get("last_name"),
                title=c.get("title"),
                company_name=c.get("company_name"),
                verification_status=c.get("verification_status"),
                hubspot_status=c.get("hubspot_status"),
            ))
    else:
        # Build from batch data
        verification_stats = {
            "total": batch.total_emails,
            "valid": batch.valid_count,
            "invalid": batch.invalid_count,
            "unknown": batch.unknown_count,
        }

    return PipelineResults(
        batch_id=batch_id,
        status=batch.status,
        search=search_stats,
        verification=verification_stats,
        hubspot=hubspot_stats,
        contacts=contacts,
    )
