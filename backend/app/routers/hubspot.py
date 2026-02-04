from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.batch import BatchJob
from app.models.hubspot_sync import HubSpotSyncLog
from app.schemas.hubspot import (
    HubSpotAuthURL,
    HubSpotContactList,
    HubSpotContact,
    HubSpotSyncRequest,
    HubSpotSyncResponse,
    HubSpotConnectionStatus,
    HubSpotDeleteRequest,
    HubSpotDeleteResponse,
    HubSpotVerifyAndEnrichRequest,
    HubSpotVerifyAndEnrichResponse,
)
from app.services.hubspot import get_hubspot_service, HubSpotError
from app.tasks.verification import process_hubspot_contacts
from app.tasks.enrichment import verify_and_enrich_hubspot_contacts

router = APIRouter(prefix="/api/hubspot", tags=["hubspot"])


@router.get("/auth", response_model=HubSpotAuthURL)
async def get_auth_url(db: Session = Depends(get_db)):
    """Get HubSpot OAuth authorization URL."""
    service = get_hubspot_service(db)
    auth_url = service.get_auth_url()
    return HubSpotAuthURL(auth_url=auth_url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Handle OAuth callback from HubSpot."""
    service = get_hubspot_service(db)

    try:
        connection = await service.exchange_code(code)

        # Ensure custom properties exist
        await service.ensure_properties_exist()

        # Redirect to frontend with success
        return RedirectResponse(url="https://frontend-lilac-chi-52.vercel.app/hubspot?connected=true")

    except HubSpotError as e:
        return RedirectResponse(url=f"https://frontend-lilac-chi-52.vercel.app/hubspot?error={str(e)}")


@router.get("/status", response_model=HubSpotConnectionStatus)
async def get_connection_status(db: Session = Depends(get_db)):
    """Check HubSpot connection status."""
    service = get_hubspot_service(db)
    connection = service.get_active_connection()

    if not connection:
        return HubSpotConnectionStatus(connected=False)

    return HubSpotConnectionStatus(
        connected=True,
        portal_id=connection.portal_id,
        expires_at=connection.expires_at,
    )


@router.delete("/disconnect")
async def disconnect(db: Session = Depends(get_db)):
    """Disconnect HubSpot integration."""
    service = get_hubspot_service(db)
    connection = service.get_active_connection()

    if connection:
        connection.is_active = False
        db.commit()

    return {"message": "Disconnected"}


@router.get("/contacts", response_model=HubSpotContactList)
async def get_contacts(
    limit: int = Query(default=100, le=100),
    after: str = Query(default=None),
    only_unverified: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Fetch contacts from HubSpot."""
    service = get_hubspot_service(db)

    try:
        result = await service.get_contacts(
            limit=limit,
            after=after,
            only_unverified=only_unverified,
        )

        contacts = [
            HubSpotContact(
                id=c["id"],
                email=c["email"],
                firstname=c.get("firstname"),
                lastname=c.get("lastname"),
                email_verification_status=c.get("email_verification_status"),
                email_verification_date=c.get("email_verification_date"),
            )
            for c in result["contacts"]
        ]

        return HubSpotContactList(
            contacts=contacts,
            total=result["total"],
            has_more=result["has_more"],
            next_cursor=result.get("next_cursor"),
        )

    except HubSpotError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify", response_model=HubSpotSyncResponse)
async def verify_contacts(
    request: HubSpotSyncRequest,
    db: Session = Depends(get_db),
):
    """
    Start verification of HubSpot contacts.

    If contacts list is provided, verify those directly.
    Otherwise, fetch all unverified contacts from HubSpot.
    """
    service = get_hubspot_service(db)

    try:
        # Use provided contacts or fetch from HubSpot
        if request.contacts:
            # Use contacts directly - no need to fetch from HubSpot
            contacts = [{"id": c.id, "email": c.email} for c in request.contacts]
        else:
            # Fetch all unverified contacts
            contacts = []
            cursor = None
            while True:
                result = await service.get_contacts(
                    limit=100,
                    after=cursor,
                    only_unverified=not request.force_reverify,
                )
                contacts.extend(result["contacts"])
                if not result["has_more"]:
                    break
                cursor = result["next_cursor"]

        if not contacts:
            return HubSpotSyncResponse(
                batch_id=0,
                status="completed",
                contacts_queued=0,
                message="No contacts to verify",
            )

        # Create batch job
        batch = BatchJob(
            filename=f"hubspot_contacts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            status="pending",
            total_emails=len(contacts),
            source="hubspot",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        # Create sync log
        sync_log = HubSpotSyncLog(
            sync_type="verify",
            status="in_progress",
            batch_id=batch.id,
        )
        db.add(sync_log)
        db.commit()

        # Queue processing task
        contact_data = [{"id": c["id"], "email": c["email"]} for c in contacts]
        process_hubspot_contacts.delay(batch.id, contact_data)

        return HubSpotSyncResponse(
            batch_id=batch.id,
            status="processing",
            contacts_queued=len(contacts),
            message=f"Verification started for {len(contacts)} contacts",
        )

    except HubSpotError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-and-enrich", response_model=HubSpotVerifyAndEnrichResponse)
async def verify_and_enrich_contacts(
    request: HubSpotVerifyAndEnrichRequest,
    db: Session = Depends(get_db),
):
    """
    Verify HubSpot contacts with ZeroBounce, then enrich valid ones with Apollo.

    This is the combined workflow:
    1. Verify emails with ZeroBounce
    2. Enrich valid emails with Apollo.io (company info, job title, phone, etc.)

    After completion, call /sync to push results back to HubSpot.
    """
    service = get_hubspot_service(db)

    try:
        # Use provided contacts or fetch from HubSpot
        if request.contacts:
            contacts = [{"id": c.id, "email": c.email} for c in request.contacts]
        else:
            # Fetch all unverified contacts
            contacts = []
            cursor = None
            while True:
                result = await service.get_contacts(
                    limit=100,
                    after=cursor,
                    only_unverified=not request.force_reverify,
                )
                contacts.extend(result["contacts"])
                if not result["has_more"]:
                    break
                cursor = result["next_cursor"]

        if not contacts:
            return HubSpotVerifyAndEnrichResponse(
                batch_id=0,
                status="completed",
                contacts_queued=0,
                message="No contacts to process",
                will_enrich=False,
            )

        # Create batch job
        batch = BatchJob(
            filename=f"hubspot_verify_enrich_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            status="pending",
            total_emails=len(contacts),
            source="hubspot",
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        # Create sync log
        sync_log = HubSpotSyncLog(
            sync_type="verify_and_enrich",
            status="in_progress",
            batch_id=batch.id,
        )
        db.add(sync_log)
        db.commit()

        # Queue combined verify + enrich task
        contact_data = [{"id": c["id"], "email": c["email"]} for c in contacts]
        verify_and_enrich_hubspot_contacts.delay(
            batch.id,
            contact_data,
            enrich_valid_only=request.enrich_valid_only,
        )

        return HubSpotVerifyAndEnrichResponse(
            batch_id=batch.id,
            status="processing",
            contacts_queued=len(contacts),
            message=f"Verification and enrichment started for {len(contacts)} contacts",
            will_enrich=True,
        )

    except HubSpotError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sync")
async def sync_results(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """
    Sync verification results back to HubSpot.

    Call this after a verification batch is completed.
    """
    service = get_hubspot_service(db)

    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="Batch not yet completed")

    if batch.source != "hubspot":
        raise HTTPException(status_code=400, detail="Batch is not from HubSpot")

    # Get verification results for this batch
    from app.models.email import EmailVerification

    verifications = (
        db.query(EmailVerification)
        .filter(EmailVerification.batch_id == batch_id)
        .all()
    )

    # Get original contact data from task result (simplified approach)
    # In production, store contact mapping in database
    # For now, we'll need the email->contact_id mapping from the original request

    updated = 0
    errors = []

    # Create sync log
    sync_log = HubSpotSyncLog(
        sync_type="sync_results",
        status="in_progress",
        batch_id=batch_id,
    )
    db.add(sync_log)
    db.commit()

    try:
        # For each verification, we need to find the contact by email
        # This is a simplified approach - ideally we'd store the mapping
        all_contacts = []
        cursor = None
        while True:
            result = await service.get_contacts(limit=100, after=cursor)
            all_contacts.extend(result["contacts"])
            if not result["has_more"]:
                break
            cursor = result["next_cursor"]

        email_to_contact = {c["email"].lower(): c["id"] for c in all_contacts}

        for v in verifications:
            contact_id = email_to_contact.get(v.email.lower())
            if contact_id:
                try:
                    success = await service.update_contact(
                        contact_id=contact_id,
                        verification_status=v.status,
                        verification_date=v.created_at,
                    )
                    if success:
                        updated += 1
                except Exception as e:
                    errors.append({"email": v.email, "error": str(e)})

        sync_log.status = "completed"
        sync_log.contacts_processed = len(verifications)
        sync_log.contacts_updated = updated
        sync_log.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "completed",
            "contacts_processed": len(verifications),
            "contacts_updated": updated,
            "errors": errors[:10] if errors else [],  # Return first 10 errors
        }

    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-enrichment")
async def sync_enrichment_results(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """
    Sync Apollo enrichment results back to HubSpot.

    Call this after a verify-and-enrich batch is completed to push
    enrichment data (job title, company, phone, LinkedIn, etc.) to HubSpot contacts.
    """
    service = get_hubspot_service(db)

    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="Batch not yet completed")

    if batch.source != "hubspot":
        raise HTTPException(status_code=400, detail="Batch is not from HubSpot")

    # Get enrichment results for this batch
    from app.models.enrichment import ContactEnrichment

    enrichments = (
        db.query(ContactEnrichment)
        .filter(ContactEnrichment.batch_id == batch_id)
        .filter(ContactEnrichment.enriched == True)
        .all()
    )

    if not enrichments:
        return {
            "status": "completed",
            "message": "No enrichment data to sync",
            "contacts_updated": 0,
        }

    # Create sync log
    sync_log = HubSpotSyncLog(
        sync_type="sync_enrichment",
        status="in_progress",
        batch_id=batch_id,
    )
    db.add(sync_log)
    db.commit()

    updated = 0
    errors = []

    try:
        # Get email to contact_id mapping from HubSpot
        all_contacts = []
        cursor = None
        while True:
            result = await service.get_contacts(limit=100, after=cursor)
            all_contacts.extend(result["contacts"])
            if not result["has_more"]:
                break
            cursor = result["next_cursor"]

        email_to_contact = {c["email"].lower(): c["id"] for c in all_contacts}

        for e in enrichments:
            contact_id = email_to_contact.get(e.email.lower())
            if contact_id:
                try:
                    enrichment_data = {
                        "title": e.title,
                        "company_name": e.company_name,
                        "phone_numbers": e.phone_numbers,
                        "linkedin_url": e.linkedin_url,
                        "seniority": e.seniority,
                        "company_size": e.company_size,
                        "company_industry": e.company_industry,
                    }
                    success = await service.update_contact_enrichment(
                        contact_id=contact_id,
                        enrichment_data=enrichment_data,
                    )
                    if success:
                        updated += 1
                except Exception as ex:
                    errors.append({"email": e.email, "error": str(ex)})

        sync_log.status = "completed"
        sync_log.contacts_processed = len(enrichments)
        sync_log.contacts_updated = updated
        sync_log.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "completed",
            "contacts_processed": len(enrichments),
            "contacts_updated": updated,
            "errors": errors[:10] if errors else [],
        }

    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete", response_model=HubSpotDeleteResponse)
async def delete_contacts(
    request: HubSpotDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    Delete contacts from HubSpot.

    This permanently removes contacts from HubSpot.
    """
    service = get_hubspot_service(db)

    if not request.contact_ids:
        raise HTTPException(status_code=400, detail="No contacts specified")

    try:
        result = await service.delete_contacts_batch(request.contact_ids)

        return HubSpotDeleteResponse(
            deleted_count=len(result["deleted"]),
            failed_count=len(result["failed"]),
            deleted=result["deleted"],
            failed=result["failed"],
        )

    except HubSpotError as e:
        raise HTTPException(status_code=400, detail=str(e))
