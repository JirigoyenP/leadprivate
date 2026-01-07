from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.email import EmailVerification
from app.services.zerobounce import get_zerobounce_service, ZeroBounceError


class VerificationService:
    def __init__(self, db: Session):
        self.db = db
        self.zerobounce = get_zerobounce_service()

    async def verify_email(
        self,
        email: str,
        batch_id: Optional[int] = None,
        use_cache: bool = True,
    ) -> dict:
        """
        Verify an email address.

        Args:
            email: Email address to verify
            batch_id: Optional batch job ID
            use_cache: Whether to use cached results (default True)

        Returns:
            Verification result dictionary
        """
        email = email.lower().strip()

        # Check cache (recent verification within 24 hours)
        if use_cache:
            cached = self._get_cached_result(email)
            if cached:
                return cached

        # Verify with ZeroBounce
        result = await self.zerobounce.verify_email(email)

        # Store result
        verification = EmailVerification(
            email=email,
            status=result["status"],
            sub_status=result.get("sub_status"),
            score=result.get("score"),
            free_email=str(result.get("free_email", "")).lower() if result.get("free_email") is not None else None,
            did_you_mean=result.get("did_you_mean"),
            domain=result.get("domain"),
            domain_age_days=result.get("domain_age_days"),
            smtp_provider=result.get("smtp_provider"),
            mx_found=str(result.get("mx_found", "")).lower() if result.get("mx_found") is not None else None,
            mx_record=result.get("mx_record"),
            batch_id=batch_id,
        )
        self.db.add(verification)
        self.db.commit()

        return result

    def _get_cached_result(self, email: str) -> Optional[dict]:
        """Get cached verification result if recent."""
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=24)

        cached = (
            self.db.query(EmailVerification)
            .filter(
                EmailVerification.email == email,
                EmailVerification.created_at >= cutoff,
            )
            .order_by(EmailVerification.created_at.desc())
            .first()
        )

        if cached:
            return {
                "email": cached.email,
                "status": cached.status,
                "sub_status": cached.sub_status,
                "score": cached.score,
                "free_email": cached.free_email == "true" if cached.free_email else None,
                "did_you_mean": cached.did_you_mean,
                "domain": cached.domain,
                "domain_age_days": cached.domain_age_days,
                "smtp_provider": cached.smtp_provider,
                "mx_found": cached.mx_found == "true" if cached.mx_found else None,
                "mx_record": cached.mx_record,
                "verified_at": cached.created_at,
                "cached": True,
            }

        return None

    async def verify_batch(
        self,
        emails: list[str],
        batch_id: Optional[int] = None,
    ) -> list[dict]:
        """Verify a batch of emails."""
        results = []
        for email in emails:
            try:
                result = await self.verify_email(email, batch_id=batch_id)
                results.append(result)
            except ZeroBounceError as e:
                results.append({
                    "email": email,
                    "status": "error",
                    "error": str(e),
                    "verified_at": datetime.utcnow(),
                })
        return results

    def get_stats(self, results: list[dict]) -> dict:
        """Calculate statistics from verification results."""
        valid = sum(1 for r in results if r.get("status") == "valid")
        invalid = sum(1 for r in results if r.get("status") == "invalid")
        unknown = sum(1 for r in results if r.get("status") in ("unknown", "catch-all"))
        errors = sum(1 for r in results if r.get("status") == "error")

        return {
            "total": len(results),
            "valid_count": valid,
            "invalid_count": invalid,
            "unknown_count": unknown,
            "error_count": errors,
        }


def get_verification_service(db: Session) -> VerificationService:
    return VerificationService(db)
