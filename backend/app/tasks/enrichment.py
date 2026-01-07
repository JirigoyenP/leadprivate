import asyncio
from datetime import datetime
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.batch import BatchJob
from app.models.enrichment import ContactEnrichment
from app.services.apollo import get_apollo_service


@celery_app.task(bind=True)
def enrich_contacts_with_apollo(self, batch_id: int, contact_data: list[dict]):
    """
    Enrich contacts with Apollo.io data after ZeroBounce verification.

    This task runs after verification is complete and only enriches
    valid email addresses to save Apollo API credits.

    Args:
        batch_id: ID of the BatchJob
        contact_data: List of contact dicts with email (and optionally contact_id, status)
    """
    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        # Update batch status
        batch.status = "enriching"
        batch.started_at = datetime.utcnow()
        db.commit()

        apollo_service = get_apollo_service()
        results = []
        enriched_count = 0
        error_count = 0

        for i, contact in enumerate(contact_data):
            email = contact.get("email")
            if not email:
                continue

            try:
                # Enrich with Apollo
                enrichment_data = asyncio.run(apollo_service.enrich_person(email))

                # Save to database
                enrichment = ContactEnrichment(
                    email=email,
                    enriched=enrichment_data.get("enriched", False),
                    first_name=enrichment_data.get("first_name"),
                    last_name=enrichment_data.get("last_name"),
                    full_name=enrichment_data.get("full_name"),
                    title=enrichment_data.get("title"),
                    headline=enrichment_data.get("headline"),
                    linkedin_url=enrichment_data.get("linkedin_url"),
                    phone_numbers=enrichment_data.get("phone_numbers"),
                    city=enrichment_data.get("city"),
                    state=enrichment_data.get("state"),
                    country=enrichment_data.get("country"),
                    employment_history=enrichment_data.get("employment_history"),
                    seniority=enrichment_data.get("seniority"),
                    departments=enrichment_data.get("departments"),
                    company_name=enrichment_data.get("company_name"),
                    company_domain=enrichment_data.get("company_domain"),
                    company_industry=enrichment_data.get("company_industry"),
                    company_size=enrichment_data.get("company_size"),
                    company_linkedin_url=enrichment_data.get("company_linkedin_url"),
                    company_phone=enrichment_data.get("company_phone"),
                    company_founded_year=enrichment_data.get("company_founded_year"),
                    company_location=enrichment_data.get("company_location"),
                    apollo_id=enrichment_data.get("apollo_id"),
                    batch_id=batch_id,
                )
                db.add(enrichment)
                db.commit()

                if enrichment_data.get("enriched"):
                    enriched_count += 1

                enrichment_data["contact_id"] = contact.get("contact_id")
                results.append(enrichment_data)

                # Update progress
                batch.processed_emails = i + 1
                db.commit()

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(contact_data),
                        "percent": int((i + 1) / len(contact_data) * 100),
                        "enriched": enriched_count,
                    },
                )

            except Exception as e:
                error_count += 1
                # Save error record
                enrichment = ContactEnrichment(
                    email=email,
                    enriched=False,
                    error_message=str(e),
                    batch_id=batch_id,
                )
                db.add(enrichment)
                db.commit()

                results.append({
                    "email": email,
                    "contact_id": contact.get("contact_id"),
                    "enriched": False,
                    "error": str(e),
                })

        # Update batch status
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "total": len(contact_data),
            "enriched": enriched_count,
            "errors": error_count,
            "results": results,
        }

    except Exception as e:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            db.commit()
        return {"error": str(e)}

    finally:
        db.close()


@celery_app.task(bind=True)
def verify_and_enrich_hubspot_contacts(
    self,
    batch_id: int,
    contact_data: list[dict],
    enrich_valid_only: bool = True,
):
    """
    Combined task: Verify contacts with ZeroBounce, then enrich valid ones with Apollo.

    This is the main workflow for HubSpot contacts:
    1. Fetch contacts from HubSpot
    2. Verify emails with ZeroBounce
    3. Enrich valid emails with Apollo
    4. Sync all results back to HubSpot

    Args:
        batch_id: ID of the BatchJob
        contact_data: List of contact dicts with id and email
        enrich_valid_only: If True, only enrich emails marked as valid
    """
    from app.services.verification import get_verification_service

    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        batch.total_emails = len(contact_data)
        db.commit()

        verification_service = get_verification_service(db)
        apollo_service = get_apollo_service()

        results = []
        valid_emails = []

        # Phase 1: Verify all emails with ZeroBounce
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "verification",
                "current": 0,
                "total": len(contact_data),
                "percent": 0,
            },
        )

        for i, contact in enumerate(contact_data):
            email = contact["email"]
            try:
                verification = asyncio.run(
                    verification_service.verify_email(email, batch_id=batch_id)
                )
                verification["contact_id"] = contact["id"]
                results.append(verification)

                # Track valid emails for enrichment
                if verification.get("status") == "valid":
                    batch.valid_count += 1
                    valid_emails.append(contact)
                elif verification.get("status") == "invalid":
                    batch.invalid_count += 1
                else:
                    batch.unknown_count += 1

                batch.processed_emails = i + 1
                db.commit()

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "phase": "verification",
                        "current": i + 1,
                        "total": len(contact_data),
                        "percent": int((i + 1) / len(contact_data) * 50),  # First 50%
                        "valid": batch.valid_count,
                        "invalid": batch.invalid_count,
                    },
                )

            except Exception as e:
                results.append({
                    "contact_id": contact["id"],
                    "email": email,
                    "status": "error",
                    "error": str(e),
                })

        # Phase 2: Enrich valid emails with Apollo
        contacts_to_enrich = valid_emails if enrich_valid_only else contact_data
        enrichments = []

        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "enrichment",
                "current": 0,
                "total": len(contacts_to_enrich),
                "percent": 50,
            },
        )

        for i, contact in enumerate(contacts_to_enrich):
            email = contact["email"]
            try:
                enrichment = asyncio.run(apollo_service.enrich_person(email))

                # Save enrichment to database
                enrichment_record = ContactEnrichment(
                    email=email,
                    enriched=enrichment.get("enriched", False),
                    first_name=enrichment.get("first_name"),
                    last_name=enrichment.get("last_name"),
                    full_name=enrichment.get("full_name"),
                    title=enrichment.get("title"),
                    headline=enrichment.get("headline"),
                    linkedin_url=enrichment.get("linkedin_url"),
                    phone_numbers=enrichment.get("phone_numbers"),
                    city=enrichment.get("city"),
                    state=enrichment.get("state"),
                    country=enrichment.get("country"),
                    employment_history=enrichment.get("employment_history"),
                    seniority=enrichment.get("seniority"),
                    departments=enrichment.get("departments"),
                    company_name=enrichment.get("company_name"),
                    company_domain=enrichment.get("company_domain"),
                    company_industry=enrichment.get("company_industry"),
                    company_size=enrichment.get("company_size"),
                    company_linkedin_url=enrichment.get("company_linkedin_url"),
                    company_phone=enrichment.get("company_phone"),
                    company_founded_year=enrichment.get("company_founded_year"),
                    company_location=enrichment.get("company_location"),
                    apollo_id=enrichment.get("apollo_id"),
                    batch_id=batch_id,
                )
                db.add(enrichment_record)
                db.commit()

                enrichment["contact_id"] = contact["id"]
                enrichments.append(enrichment)

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "phase": "enrichment",
                        "current": i + 1,
                        "total": len(contacts_to_enrich),
                        "percent": 50 + int((i + 1) / len(contacts_to_enrich) * 50),
                        "enriched": sum(1 for e in enrichments if e.get("enriched")),
                    },
                )

            except Exception as e:
                enrichments.append({
                    "contact_id": contact["id"],
                    "email": email,
                    "enriched": False,
                    "error": str(e),
                })

        # Complete
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "verification": {
                "total": len(contact_data),
                "valid": batch.valid_count,
                "invalid": batch.invalid_count,
                "unknown": batch.unknown_count,
            },
            "enrichment": {
                "total": len(contacts_to_enrich),
                "enriched": sum(1 for e in enrichments if e.get("enriched")),
            },
            "results": results,
            "enrichments": enrichments,
        }

    except Exception as e:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            db.commit()
        return {"error": str(e)}

    finally:
        db.close()
