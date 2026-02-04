"""
Lead manager service - upserts leads from verification/enrichment results,
handles backfill from existing data.

Lead upsert by email: if the same email comes from HubSpot and CSV,
one Lead record is created/updated.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.models.email import EmailVerification
from app.models.enrichment import ContactEnrichment
from app.services.scoring import score_and_update_lead

logger = logging.getLogger(__name__)


def upsert_lead_from_verification(
    db: Session,
    email: str,
    verification: EmailVerification,
    source: str = "csv",
) -> Lead:
    """
    Create or update a Lead record after email verification.
    Automatically scores the lead.
    """
    lead = db.query(Lead).filter(Lead.email == email.lower().strip()).first()

    if lead is None:
        lead = Lead(email=email.lower().strip(), source=source)
        db.add(lead)

    lead.verification_status = verification.status
    lead.verification_sub_status = verification.sub_status
    lead.verification_score = verification.score
    lead.latest_verification_id = verification.id

    # Score the lead
    score_and_update_lead(lead, db)

    db.commit()
    db.refresh(lead)
    return lead


def upsert_lead_from_enrichment(
    db: Session,
    email: str,
    enrichment: ContactEnrichment,
    source: Optional[str] = None,
) -> Lead:
    """
    Create or update a Lead record after Apollo enrichment.
    Automatically scores the lead.
    """
    lead = db.query(Lead).filter(Lead.email == email.lower().strip()).first()

    if lead is None:
        lead = Lead(email=email.lower().strip(), source=source or "csv")
        db.add(lead)

    if source:
        lead.source = source

    lead.enriched = enrichment.enriched
    lead.latest_enrichment_id = enrichment.id

    if enrichment.enriched:
        lead.first_name = enrichment.first_name or lead.first_name
        lead.last_name = enrichment.last_name or lead.last_name
        lead.full_name = enrichment.full_name or lead.full_name
        lead.title = enrichment.title or lead.title
        lead.headline = enrichment.headline or lead.headline
        lead.linkedin_url = enrichment.linkedin_url or lead.linkedin_url
        lead.seniority = enrichment.seniority or lead.seniority
        lead.city = enrichment.city or lead.city
        lead.state = enrichment.state or lead.state
        lead.country = enrichment.country or lead.country
        lead.departments = enrichment.departments or lead.departments
        lead.phone_numbers = enrichment.phone_numbers or lead.phone_numbers
        lead.company_name = enrichment.company_name or lead.company_name
        lead.company_domain = enrichment.company_domain or lead.company_domain
        lead.company_industry = enrichment.company_industry or lead.company_industry
        lead.company_size = enrichment.company_size or lead.company_size
        lead.company_location = enrichment.company_location or lead.company_location

        # Extract primary phone
        if enrichment.phone_numbers and len(enrichment.phone_numbers) > 0:
            if isinstance(enrichment.phone_numbers[0], dict):
                lead.phone = enrichment.phone_numbers[0].get("sanitized_number") or enrichment.phone_numbers[0].get("number")
            else:
                lead.phone = str(enrichment.phone_numbers[0])

    # Score the lead
    score_and_update_lead(lead, db)

    db.commit()
    db.refresh(lead)
    return lead


def backfill_leads(db: Session) -> dict:
    """
    Populate leads table from existing EmailVerification and ContactEnrichment data.
    Returns stats about the backfill operation.
    """
    created = 0
    updated = 0
    errors = 0

    # Get all unique emails from verifications (most recent first)
    verifications = (
        db.query(EmailVerification)
        .order_by(EmailVerification.created_at.desc())
        .all()
    )

    seen_emails = set()
    for v in verifications:
        email = v.email.lower().strip()
        if email in seen_emails:
            continue
        seen_emails.add(email)

        try:
            lead = db.query(Lead).filter(Lead.email == email).first()
            if lead is None:
                lead = Lead(email=email, source="csv")
                db.add(lead)
                created += 1
            else:
                updated += 1

            lead.verification_status = v.status
            lead.verification_sub_status = v.sub_status
            lead.verification_score = v.score
            lead.latest_verification_id = v.id
        except Exception as e:
            logger.error(f"Error backfilling verification for {email}: {e}")
            errors += 1

    db.flush()

    # Now layer enrichment data on top
    enrichments = (
        db.query(ContactEnrichment)
        .filter(ContactEnrichment.enriched == True)
        .order_by(ContactEnrichment.created_at.desc())
        .all()
    )

    enriched_emails = set()
    for e in enrichments:
        email = e.email.lower().strip()
        if email in enriched_emails or email.endswith("@pending.local"):
            continue
        enriched_emails.add(email)

        try:
            lead = db.query(Lead).filter(Lead.email == email).first()
            if lead is None:
                lead = Lead(email=email, source="csv")
                db.add(lead)
                created += 1

            lead.enriched = True
            lead.latest_enrichment_id = e.id
            lead.first_name = e.first_name or lead.first_name
            lead.last_name = e.last_name or lead.last_name
            lead.full_name = e.full_name or lead.full_name
            lead.title = e.title or lead.title
            lead.headline = e.headline or lead.headline
            lead.linkedin_url = e.linkedin_url or lead.linkedin_url
            lead.seniority = e.seniority or lead.seniority
            lead.city = e.city or lead.city
            lead.state = e.state or lead.state
            lead.country = e.country or lead.country
            lead.departments = e.departments or lead.departments
            lead.phone_numbers = e.phone_numbers or lead.phone_numbers
            lead.company_name = e.company_name or lead.company_name
            lead.company_domain = e.company_domain or lead.company_domain
            lead.company_industry = e.company_industry or lead.company_industry
            lead.company_size = e.company_size or lead.company_size
            lead.company_location = e.company_location or lead.company_location

            if e.phone_numbers and len(e.phone_numbers) > 0:
                if isinstance(e.phone_numbers[0], dict):
                    lead.phone = e.phone_numbers[0].get("sanitized_number") or e.phone_numbers[0].get("number")
                else:
                    lead.phone = str(e.phone_numbers[0])
        except Exception as ex:
            logger.error(f"Error backfilling enrichment for {email}: {ex}")
            errors += 1

    db.flush()

    # Score all leads
    from app.services.scoring import get_active_config, score_and_update_lead
    config = get_active_config(db)
    all_leads = db.query(Lead).all()
    for lead in all_leads:
        score_and_update_lead(lead, db, config)

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "total_leads": db.query(Lead).count(),
    }
