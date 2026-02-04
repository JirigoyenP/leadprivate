"""
One-Click Pipeline Celery task: Apollo Search → ZeroBounce Verify → HubSpot Push.
"""

import asyncio
import logging
from datetime import datetime
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.batch import BatchJob
from app.models.enrichment import ContactEnrichment
from app.services.apollo import get_apollo_service
from app.services.verification import get_verification_service
from app.services.hubspot import get_hubspot_service
from app.services.lead_manager import upsert_lead_from_verification, upsert_lead_from_enrichment

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_oneclick_pipeline(self, batch_id: int, search_criteria: dict):
    """
    Full one-click pipeline: Apollo Search → ZeroBounce Verify → HubSpot Push.

    Args:
        batch_id: BatchJob ID for tracking
        search_criteria: Dict with person_titles, q_organization_domains,
                         person_locations, person_seniorities, max_results
    """
    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        db.commit()

        apollo_service = get_apollo_service()
        verification_service = get_verification_service(db)
        hubspot_service = get_hubspot_service(db)

        # Ensure custom HubSpot properties exist
        try:
            asyncio.run(hubspot_service.ensure_properties_exist())
        except Exception as e:
            logger.warning(f"Failed to ensure HubSpot properties: {e}")

        max_results = search_criteria.get("max_results", 25)

        # ── Phase 1: Apollo Search (0–20%) ──
        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "search",
                "phase_label": "Searching Apollo",
                "current": 0,
                "total": 0,
                "percent": 0,
            },
        )

        all_contacts = []
        page = 1
        per_page = min(max_results, 100)

        while len(all_contacts) < max_results:
            try:
                result = asyncio.run(
                    apollo_service.search_people(
                        person_titles=search_criteria.get("person_titles") or None,
                        q_organization_domains=search_criteria.get("q_organization_domains") or None,
                        person_locations=search_criteria.get("person_locations") or None,
                        person_seniorities=search_criteria.get("person_seniorities") or None,
                        per_page=per_page,
                        page=page,
                    )
                )
            except Exception as e:
                logger.error(f"Apollo search failed on page {page}: {e}")
                break

            contacts = result.get("contacts", [])
            if not contacts:
                break

            all_contacts.extend(contacts)
            total_available = result.get("total_entries", 0)

            self.update_state(
                state="PROGRESS",
                meta={
                    "phase": "search",
                    "phase_label": "Searching Apollo",
                    "current": len(all_contacts),
                    "total": min(max_results, total_available),
                    "percent": min(20, int(len(all_contacts) / max(max_results, 1) * 20)),
                },
            )

            if page >= result.get("total_pages", 1):
                break
            page += 1

        # Trim to max_results
        all_contacts = all_contacts[:max_results]

        batch.total_emails = len(all_contacts)
        db.commit()

        if not all_contacts:
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            db.commit()
            return {
                "batch_id": batch_id,
                "status": "completed",
                "search": {"total_found": 0},
                "verification": {},
                "hubspot": {},
                "contacts": [],
            }

        # ── Phase 2: ZeroBounce Verification (20–70%) ──
        total = len(all_contacts)
        valid_contacts = []
        contact_results = []  # Track per-contact results

        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "verification",
                "phase_label": "Verifying emails",
                "current": 0,
                "total": total,
                "percent": 20,
            },
        )

        for i, contact in enumerate(all_contacts):
            email = contact["email"]
            verification_status = "unknown"

            try:
                vresult = asyncio.run(
                    verification_service.verify_email(email, batch_id=batch_id)
                )
                verification_status = vresult.get("status", "unknown")

                # Upsert lead
                try:
                    from app.models.email import EmailVerification
                    verification_record = (
                        db.query(EmailVerification)
                        .filter(EmailVerification.email == email.lower().strip())
                        .order_by(EmailVerification.created_at.desc())
                        .first()
                    )
                    if verification_record:
                        upsert_lead_from_verification(db, email, verification_record, source="apollo")
                except Exception as e:
                    logger.warning(f"Failed to upsert lead for {email}: {e}")

                if verification_status == "valid":
                    batch.valid_count += 1
                    valid_contacts.append(contact)
                elif verification_status == "invalid":
                    batch.invalid_count += 1
                else:
                    batch.unknown_count += 1

            except Exception as e:
                logger.error(f"Verification error for {email}: {e}")

            contact_results.append({
                "email": email,
                "first_name": contact.get("first_name"),
                "last_name": contact.get("last_name"),
                "title": contact.get("title"),
                "company_name": contact.get("company_name"),
                "verification_status": verification_status,
                "hubspot_status": None,
            })

            batch.processed_emails = i + 1
            db.commit()

            self.update_state(
                state="PROGRESS",
                meta={
                    "phase": "verification",
                    "phase_label": "Verifying emails",
                    "current": i + 1,
                    "total": total,
                    "percent": 20 + int((i + 1) / total * 50),
                },
            )

        # ── Phase 3: HubSpot Push (70–100%) — valid emails only ──
        pushed_count = 0
        push_failed = 0
        push_total = len(valid_contacts)

        self.update_state(
            state="PROGRESS",
            meta={
                "phase": "hubspot_push",
                "phase_label": "Pushing to HubSpot",
                "current": 0,
                "total": push_total,
                "percent": 70,
            },
        )

        for i, contact in enumerate(valid_contacts):
            email = contact["email"]
            hubspot_status = "failed"

            try:
                result = asyncio.run(
                    hubspot_service.create_contact(contact)
                )
                hubspot_status = result.get("status", "failed")
                if hubspot_status in ("created", "updated"):
                    pushed_count += 1
                else:
                    push_failed += 1
            except Exception as e:
                logger.error(f"HubSpot push error for {email}: {e}")
                push_failed += 1

            # Store enrichment record for the contact
            try:
                enrichment_record = ContactEnrichment(
                    email=email,
                    enriched=contact.get("enriched", True),
                    first_name=contact.get("first_name"),
                    last_name=contact.get("last_name"),
                    full_name=contact.get("full_name"),
                    title=contact.get("title"),
                    headline=contact.get("headline"),
                    linkedin_url=contact.get("linkedin_url"),
                    phone_numbers=contact.get("phone_numbers"),
                    city=contact.get("city"),
                    state=contact.get("state"),
                    country=contact.get("country"),
                    seniority=contact.get("seniority"),
                    departments=contact.get("departments"),
                    company_name=contact.get("company_name"),
                    company_domain=contact.get("company_domain"),
                    company_industry=contact.get("company_industry"),
                    company_size=contact.get("company_size"),
                    company_linkedin_url=contact.get("company_linkedin_url"),
                    company_phone=contact.get("company_phone"),
                    company_founded_year=contact.get("company_founded_year"),
                    company_location=contact.get("company_location"),
                    apollo_id=contact.get("apollo_id"),
                    batch_id=batch_id,
                )
                db.add(enrichment_record)
                db.commit()
                db.refresh(enrichment_record)

                upsert_lead_from_enrichment(db, email, enrichment_record, source="apollo")
            except Exception as e:
                logger.warning(f"Failed to store enrichment for {email}: {e}")

            # Update the per-contact result
            for cr in contact_results:
                if cr["email"] == email:
                    cr["hubspot_status"] = hubspot_status
                    break

            self.update_state(
                state="PROGRESS",
                meta={
                    "phase": "hubspot_push",
                    "phase_label": "Pushing to HubSpot",
                    "current": i + 1,
                    "total": push_total,
                    "percent": 70 + int((i + 1) / max(push_total, 1) * 30),
                },
            )

        # ── Complete ──
        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "search": {
                "total_found": len(all_contacts),
            },
            "verification": {
                "total": total,
                "valid": batch.valid_count,
                "invalid": batch.invalid_count,
                "unknown": batch.unknown_count,
            },
            "hubspot": {
                "pushed": pushed_count,
                "failed": push_failed,
                "total": push_total,
            },
            "contacts": contact_results,
        }

    except Exception as e:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            db.commit()
        logger.error(f"One-click pipeline failed for batch {batch_id}: {e}")
        return {"error": str(e)}

    finally:
        db.close()
