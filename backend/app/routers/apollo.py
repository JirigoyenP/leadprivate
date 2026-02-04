from fastapi import APIRouter, HTTPException
from app.schemas.apollo import (
    ApolloEnrichRequest,
    ApolloEnrichResponse,
    ApolloBulkEnrichRequest,
    ApolloBulkEnrichResponse,
    ApolloOrganizationRequest,
    ApolloOrganizationResponse,
)
from app.services.apollo import get_apollo_service, ApolloError

router = APIRouter(prefix="/api/apollo", tags=["apollo"])


@router.post("/enrich", response_model=ApolloEnrichResponse)
async def enrich_person(request: ApolloEnrichRequest):
    """
    Enrich a single contact by email using Apollo.io.

    Returns company and contact data including:
    - Job title and seniority
    - Phone numbers
    - LinkedIn profile
    - Company information
    - Employment history
    """
    service = get_apollo_service()

    try:
        result = await service.enrich_person(request.email)
        return ApolloEnrichResponse(**result)
    except ApolloError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/enrich/bulk", response_model=ApolloBulkEnrichResponse)
async def enrich_bulk(request: ApolloBulkEnrichRequest):
    """
    Enrich multiple contacts by email.

    Note: Large batches may take some time to process.
    For very large batches, consider using the async HubSpot enrichment flow.
    """
    if len(request.emails) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 emails per request. Use HubSpot flow for larger batches."
        )

    service = get_apollo_service()

    try:
        results = await service.enrich_bulk(request.emails)

        enriched_count = sum(1 for r in results if r.get("enriched", False))
        not_found_count = len(results) - enriched_count

        return ApolloBulkEnrichResponse(
            results=[ApolloEnrichResponse(**r) for r in results],
            total=len(results),
            enriched_count=enriched_count,
            not_found_count=not_found_count,
        )
    except ApolloError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/organization", response_model=ApolloOrganizationResponse)
async def enrich_organization(request: ApolloOrganizationRequest):
    """
    Get company/organization data by domain.

    Returns company information including:
    - Company name and industry
    - Employee count
    - Founded year
    - Location
    - LinkedIn and phone
    """
    service = get_apollo_service()

    try:
        result = await service.get_organization(request.domain)
        return ApolloOrganizationResponse(**result)
    except ApolloError as e:
        raise HTTPException(status_code=400, detail=str(e))
