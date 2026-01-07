import httpx
from typing import Optional
from datetime import datetime
from app.config import get_settings


class ZeroBounceError(Exception):
    """Custom exception for ZeroBounce API errors."""
    pass


class ZeroBounceService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.zerobounce_base_url
        self.api_key = self.settings.zerobounce_api_key

    async def verify_email(self, email: str, ip_address: Optional[str] = None) -> dict:
        """
        Verify a single email address using ZeroBounce API.

        Args:
            email: Email address to verify
            ip_address: Optional IP address for additional validation

        Returns:
            Dictionary with verification results
        """
        if not self.api_key:
            raise ZeroBounceError("ZeroBounce API key not configured")

        params = {
            "api_key": self.api_key,
            "email": email,
        }
        if ip_address:
            params["ip_address"] = ip_address

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/validate",
                params=params,
            )

            if response.status_code != 200:
                raise ZeroBounceError(f"API request failed: {response.status_code}")

            data = response.json()

            if "error" in data:
                raise ZeroBounceError(data["error"])

            return self._parse_response(email, data)

    async def get_credits(self) -> dict:
        """Get remaining API credits."""
        if not self.api_key:
            raise ZeroBounceError("ZeroBounce API key not configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/getcredits",
                params={"api_key": self.api_key},
            )

            if response.status_code != 200:
                raise ZeroBounceError(f"API request failed: {response.status_code}")

            return response.json()

    def _parse_response(self, email: str, data: dict) -> dict:
        """Parse ZeroBounce API response into our standard format."""
        return {
            "email": email,
            "status": data.get("status", "unknown").lower(),
            "sub_status": data.get("sub_status"),
            "score": self._parse_score(data.get("mx_record")),
            "free_email": data.get("free_email") == "true",
            "did_you_mean": data.get("did_you_mean") or None,
            "domain": data.get("domain"),
            "domain_age_days": self._parse_int(data.get("domain_age_days")),
            "smtp_provider": data.get("smtp_provider"),
            "mx_found": data.get("mx_found") == "true",
            "mx_record": data.get("mx_record"),
            "verified_at": datetime.utcnow(),
        }

    def _parse_score(self, mx_record: Optional[str]) -> Optional[int]:
        """ZeroBounce doesn't return a direct score, derive from status."""
        # This is a placeholder - actual scoring would depend on status
        return None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        """Safely parse a string to int."""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


# Singleton instance
_zerobounce_service: Optional[ZeroBounceService] = None


def get_zerobounce_service() -> ZeroBounceService:
    global _zerobounce_service
    if _zerobounce_service is None:
        _zerobounce_service = ZeroBounceService()
    return _zerobounce_service
