from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.schemas.email import (
    EmailVerifyRequest,
    EmailVerifyResponse,
    BatchVerifyRequest,
    BatchVerifyResponse,
)
from app.services.verification import get_verification_service
from app.services.zerobounce import ZeroBounceError

router = APIRouter(prefix="/api/verify", tags=["verification"])


@router.post("/single", response_model=EmailVerifyResponse)
async def verify_single_email(
    request: EmailVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify a single email address.

    Returns detailed verification status from ZeroBounce.
    Results are cached for 24 hours.
    """
    service = get_verification_service(db)

    try:
        result = await service.verify_email(request.email)
        return EmailVerifyResponse(
            email=result["email"],
            status=result["status"],
            sub_status=result.get("sub_status"),
            score=result.get("score"),
            free_email=result.get("free_email"),
            did_you_mean=result.get("did_you_mean"),
            domain=result.get("domain"),
            domain_age_days=result.get("domain_age_days"),
            smtp_provider=result.get("smtp_provider"),
            mx_found=result.get("mx_found"),
            mx_record=result.get("mx_record"),
            verified_at=result.get("verified_at", datetime.utcnow()),
        )
    except ZeroBounceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch", response_model=BatchVerifyResponse)
async def verify_batch_emails(
    request: BatchVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify multiple email addresses (up to 100).

    For larger batches, use the /api/batch/upload endpoint with CSV upload.
    """
    if len(request.emails) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 emails per batch. Use CSV upload for larger batches.",
        )

    service = get_verification_service(db)

    try:
        results = await service.verify_batch([str(e) for e in request.emails])
        stats = service.get_stats(results)

        response_results = []
        for r in results:
            if r.get("status") != "error":
                response_results.append(
                    EmailVerifyResponse(
                        email=r["email"],
                        status=r["status"],
                        sub_status=r.get("sub_status"),
                        score=r.get("score"),
                        free_email=r.get("free_email"),
                        did_you_mean=r.get("did_you_mean"),
                        domain=r.get("domain"),
                        domain_age_days=r.get("domain_age_days"),
                        smtp_provider=r.get("smtp_provider"),
                        mx_found=r.get("mx_found"),
                        mx_record=r.get("mx_record"),
                        verified_at=r.get("verified_at", datetime.utcnow()),
                    )
                )

        return BatchVerifyResponse(
            results=response_results,
            total=stats["total"],
            valid_count=stats["valid_count"],
            invalid_count=stats["invalid_count"],
            unknown_count=stats["unknown_count"],
        )
    except ZeroBounceError as e:
        raise HTTPException(status_code=400, detail=str(e))
