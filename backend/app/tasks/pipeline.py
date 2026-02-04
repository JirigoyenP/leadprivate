"""
Full pipeline Celery task: verify -> enrich -> score.
"""

import asyncio
import logging
from datetime import datetime
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.batch import BatchJob
from app.models.enrichment import ContactEnrichment
from app.services.verification import get_verification_service
from app.services.apollo import get_apollo_service
from app.services.lead_manager import upsert_lead_from_verification, upsert_lead_from_enrichment

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_lead_pipeline(self, batch_id: int, contact_data: list[dict]):
    """
    Full pipeline: verify -> enrich -> score for a list of leads.

    Args:
        batch_id: BatchJob ID for tracking
        contact_data: List of dicts with 'email' and optionally 'id'
    """
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

        valid_contacts = []
        total = len(contact_data)

        # Phase 1: Verify
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "verification",
                "current": 0,
                "total": total,
                "percent": 0,
            },
        )

        for i, contact in enumerate(contact_data):
            email = contact["email"]
            try:
                result = asyncio.run(
                    verification_service.verify_email(email, batch_id=batch_id)
                )

                # Upsert lead from verification
                try:
                    from app.models.email import EmailVerification
                    verification_record = (
                        db.query(EmailVerification)
                        .filter(EmailVerification.email == email.lower().strip())
                        .order_by(EmailVerification.created_at.desc())
                        .first()
                    )
                    if verification_record:
                        upsert_lead_from_verification(db, email, verification_record, source="csv")
                except Exception as e:
                    logger.warning(f"Failed to upsert lead from verification for {email}: {e}")

                if result.get("status") == "valid":
                    batch.valid_count += 1
                    valid_contacts.append(contact)
                elif result.get("status") == "invalid":
                    batch.invalid_count += 1
                else:
                    batch.unknown_count += 1

                batch.processed_emails = i + 1
                db.commit()

            except Exception as e:
                logger.error(f"Pipeline verification error for {email}: {e}")

            self.update_state(
                state="PROGRESS",
                meta={
                    "phase": "verification",
                    "current": i + 1,
                    "total": total,
                    "percent": int((i + 1) / total * 33),
                },
            )

        # Phase 2: Enrich valid contacts
        enrich_total = len(valid_contacts)
        enriched_count = 0

        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "enrichment",
                "current": 0,
                "total": enrich_total,
                "percent": 33,
            },
        )

        for i, contact in enumerate(valid_contacts):
            email = contact["email"]
            try:
                enrichment_data = asyncio.run(apollo_service.enrich_person(email))

                enrichment_record = ContactEnrichment(
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
                db.add(enrichment_record)
                db.commit()
                db.refresh(enrichment_record)

                # Upsert lead from enrichment (also triggers scoring)
                try:
                    upsert_lead_from_enrichment(db, email, enrichment_record, source="csv")
                except Exception as e:
                    logger.warning(f"Failed to upsert lead from enrichment for {email}: {e}")

                if enrichment_data.get("enriched"):
                    enriched_count += 1

            except Exception as e:
                logger.error(f"Pipeline enrichment error for {email}: {e}")

            self.update_state(
                state="PROGRESS",
                meta={
                    "phase": "enrichment",
                    "current": i + 1,
                    "total": enrich_total,
                    "percent": 33 + int((i + 1) / max(enrich_total, 1) * 34),
                },
            )

        # Phase 3: Scoring is done automatically in upsert, but rescore all for safety
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "scoring",
                "current": 0,
                "total": total,
                "percent": 67,
            },
        )

        from app.services.scoring import rescore_all_leads
        rescored = rescore_all_leads(db)

        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "scoring",
                "current": rescored,
                "total": rescored,
                "percent": 100,
            },
        )

        # Complete
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "verification": {
                "total": total,
                "valid": batch.valid_count,
                "invalid": batch.invalid_count,
                "unknown": batch.unknown_count,
            },
            "enrichment": {
                "total": enrich_total,
                "enriched": enriched_count,
            },
            "scoring": {
                "rescored": rescored,
            },
        }

    except Exception as e:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            db.commit()
        logger.error(f"Pipeline failed for batch {batch_id}: {e}")
        return {"error": str(e)}

    finally:
        db.close()
