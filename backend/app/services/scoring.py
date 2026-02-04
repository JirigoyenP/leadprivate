"""
Lead scoring service - scores leads 0-100 based on configurable criteria.


Scoring categories:
- Email quality (25pts): valid=25, catch-all=10, invalid=0
- Seniority (25pts): C-level=25, VP=20, Director=15, Manager=10, other=5
- Company fit (25pts): size in ideal range + industry match
- Data completeness (25pts): phone=8, linkedin=8, company=5, title=4
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.lead import Lead, ScoringConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "weights": {
        "email_quality": 25,
        "seniority": 25,
        "company_fit": 25,
        "data_completeness": 25,
    },
    "seniority_scores": {
        "c_suite": 25,
        "vp": 20,
        "director": 15,
        "manager": 10,
        "other": 5,
    },
    "ideal_company_size": {
        "min": 50,
        "max": 5000,
    },
    "target_industries": [],
}

# Seniority keyword mapping
SENIORITY_MAP = {
    "c_suite": ["c-suite", "c-level", "ceo", "cto", "cfo", "coo", "cmo", "cio", "chief", "founder", "co-founder", "owner"],
    "vp": ["vp", "vice president", "vice-president", "svp", "evp"],
    "director": ["director"],
    "manager": ["manager", "head of", "lead", "senior manager", "team lead"],
}


def get_active_config(db: Session) -> dict:
    """Get the active scoring configuration, or use defaults."""
    config_record = (
        db.query(ScoringConfig)
        .filter(ScoringConfig.is_active == True)
        .order_by(ScoringConfig.updated_at.desc())
        .first()
    )
    if config_record and config_record.config:
        return config_record.config
    return DEFAULT_CONFIG


def classify_seniority(seniority: Optional[str], title: Optional[str]) -> str:
    """Classify a lead's seniority level from seniority field or job title."""
    text = ""
    if seniority:
        text += seniority.lower()
    if title:
        text += " " + title.lower()

    if not text.strip():
        return "other"

    for level, keywords in SENIORITY_MAP.items():
        for kw in keywords:
            if kw in text:
                return level
    return "other"


def score_lead(lead: Lead, config: Optional[dict] = None) -> tuple:
    """
    Score a single lead 0-100.

    Returns:
        Tuple of (total_score, breakdown_dict)
    """
    if config is None:
        config = DEFAULT_CONFIG

    weights = config.get("weights", DEFAULT_CONFIG["weights"])
    seniority_scores = config.get("seniority_scores", DEFAULT_CONFIG["seniority_scores"])
    ideal_size = config.get("ideal_company_size", DEFAULT_CONFIG["ideal_company_size"])
    target_industries = config.get("target_industries", [])

    breakdown = {}

    # 1. Email quality
    max_email = weights.get("email_quality", 25)
    if lead.verification_status == "valid":
        breakdown["email_quality"] = max_email
    elif lead.verification_status == "catch-all":
        breakdown["email_quality"] = int(max_email * 0.4)
    elif lead.verification_status in ("unknown", None):
        breakdown["email_quality"] = int(max_email * 0.2)
    else:  # invalid, spamtrap, abuse, do_not_mail
        breakdown["email_quality"] = 0

    # 2. Seniority
    max_seniority = weights.get("seniority", 25)
    seniority_level = classify_seniority(lead.seniority, lead.title)
    breakdown["seniority"] = seniority_scores.get(seniority_level, seniority_scores.get("other", 5))
    # Cap at max weight
    breakdown["seniority"] = min(breakdown["seniority"], max_seniority)

    # 3. Company fit
    max_company = weights.get("company_fit", 25)
    company_score = 0

    # Company size fit (up to 60% of company_fit weight)
    if lead.company_size is not None:
        size_min = ideal_size.get("min", 50)
        size_max = ideal_size.get("max", 5000)
        if size_min <= lead.company_size <= size_max:
            company_score += int(max_company * 0.6)
        elif lead.company_size > 0:
            # Partial credit: closer to range = more points
            if lead.company_size < size_min:
                ratio = lead.company_size / size_min
            else:
                ratio = size_max / lead.company_size
            company_score += int(max_company * 0.6 * max(ratio, 0.2))

    # Industry match (up to 40% of company_fit weight)
    if target_industries and lead.company_industry:
        industry_lower = lead.company_industry.lower()
        if any(ind.lower() in industry_lower for ind in target_industries):
            company_score += int(max_company * 0.4)
    elif not target_industries:
        # No target industries configured = give full industry points
        company_score += int(max_company * 0.4)

    breakdown["company_fit"] = min(company_score, max_company)

    # 4. Data completeness
    max_completeness = weights.get("data_completeness", 25)
    completeness = 0

    # Phone (8/25 of completeness weight)
    phone_weight = int(max_completeness * 8 / 25)
    if lead.phone or (lead.phone_numbers and len(lead.phone_numbers) > 0):
        completeness += phone_weight

    # LinkedIn (8/25)
    linkedin_weight = int(max_completeness * 8 / 25)
    if lead.linkedin_url:
        completeness += linkedin_weight

    # Company (5/25)
    company_weight = int(max_completeness * 5 / 25)
    if lead.company_name:
        completeness += company_weight

    # Title (4/25)
    title_weight = int(max_completeness * 4 / 25)
    if lead.title:
        completeness += title_weight

    breakdown["data_completeness"] = min(completeness, max_completeness)

    total = sum(breakdown.values())
    total = max(0, min(100, total))

    return total, breakdown


def score_and_update_lead(lead: Lead, db: Session, config: Optional[dict] = None) -> Lead:
    """Score a lead and update its database record."""
    if config is None:
        config = get_active_config(db)

    total, breakdown = score_lead(lead, config)
    lead.lead_score = total
    lead.score_breakdown = breakdown
    return lead


def rescore_all_leads(db: Session) -> int:
    """Recalculate scores for all leads. Returns count of leads rescored."""
    config = get_active_config(db)
    leads = db.query(Lead).all()
    count = 0
    for lead in leads:
        score_and_update_lead(lead, db, config)
        count += 1
    db.commit()
    return count
