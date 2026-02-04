import httpx
from typing import Optional
from datetime import datetime
from app.config import get_settings


class ApolloError(Exception):
    """Custom exception for Apollo API errors."""
    pass


class ApolloService:
    """
    Apollo.io API service for contact enrichment.

    Apollo provides company and contact data enrichment including:
    - Company information (name, domain, industry, size, etc.)
    - Contact details (job title, phone, LinkedIn, etc.)
    - Employment history
    """

    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.apollo_api_key

    async def enrich_person(self, email: str) -> dict:
        """
        Enrich a single person/contact using their email address.

        Args:
            email: Email address to enrich

        Returns:
            Dictionary with enriched contact data
        """
        if not self.api_key:
            raise ApolloError("Apollo API key not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/people/match",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                json={
                    "api_key": self.api_key,
                    "email": email,
                },
            )

            if response.status_code == 401:
                raise ApolloError("Invalid Apollo API key")

            if response.status_code == 429:
                raise ApolloError("Apollo API rate limit exceeded")

            if response.status_code != 200:
                raise ApolloError(f"Apollo API request failed: {response.status_code}")

            data = response.json()

            if not data.get("person"):
                return self._empty_result(email)

            return self._parse_person_response(email, data["person"])

    async def enrich_bulk(self, emails: list[str]) -> list[dict]:
        """
        Enrich multiple contacts by email.

        Note: Apollo's bulk enrichment has limits. For large batches,
        consider using the async file-based enrichment API.

        Args:
            emails: List of email addresses to enrich

        Returns:
            List of enriched contact dictionaries
        """
        if not self.api_key:
            raise ApolloError("Apollo API key not configured")

        results = []

        # Apollo doesn't have a true bulk endpoint for person match,
        # so we process one by one (with potential for batching via their
        # bulk_people_match endpoint in the future)
        for email in emails:
            try:
                result = await self.enrich_person(email)
                results.append(result)
            except ApolloError as e:
                results.append({
                    "email": email,
                    "enriched": False,
                    "error": str(e),
                    "enriched_at": datetime.utcnow(),
                })

        return results

    async def get_credits(self) -> dict:
        """
        Check Apollo API credit balance via the health endpoint.

        Returns:
            Dictionary with credit info and connection status
        """
        if not self.api_key:
            return {"credits": None, "status": "not_configured"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/auth/health",
                    headers={
                        "Content-Type": "application/json",
                        "Cache-Control": "no-cache",
                    },
                    json={"api_key": self.api_key},
                )

                if response.status_code != 200:
                    return {"credits": None, "status": "error", "error": f"HTTP {response.status_code}"}

                data = response.json()
                return {
                    "credits": data.get("plan_credits_remaining"),
                    "plan": data.get("plan_name"),
                    "status": "connected",
                }
        except Exception as e:
            return {"credits": None, "status": "error", "error": str(e)}

    async def get_organization(self, domain: str) -> dict:
        """
        Get organization/company data by domain.

        Args:
            domain: Company domain (e.g., 'google.com')

        Returns:
            Dictionary with company information
        """
        if not self.api_key:
            raise ApolloError("Apollo API key not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/organizations/enrich",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                json={
                    "api_key": self.api_key,
                    "domain": domain,
                },
            )

            if response.status_code != 200:
                raise ApolloError(f"Apollo API request failed: {response.status_code}")

            data = response.json()

            if not data.get("organization"):
                return {"domain": domain, "enriched": False}

            return self._parse_organization_response(domain, data["organization"])

    def _parse_person_response(self, email: str, person: dict) -> dict:
        """Parse Apollo person response into our standard format."""
        organization = person.get("organization") or {}

        return {
            "email": email,
            "enriched": True,
            # Personal info
            "first_name": person.get("first_name"),
            "last_name": person.get("last_name"),
            "full_name": person.get("name"),
            "title": person.get("title"),
            "headline": person.get("headline"),
            "linkedin_url": person.get("linkedin_url"),
            "phone_numbers": person.get("phone_numbers") or [],
            "city": person.get("city"),
            "state": person.get("state"),
            "country": person.get("country"),
            # Employment info
            "employment_history": self._parse_employment_history(person.get("employment_history") or []),
            "seniority": person.get("seniority"),
            "departments": person.get("departments") or [],
            # Company info
            "company_name": organization.get("name"),
            "company_domain": organization.get("primary_domain") or organization.get("website_url"),
            "company_industry": organization.get("industry"),
            "company_size": organization.get("estimated_num_employees"),
            "company_linkedin_url": organization.get("linkedin_url"),
            "company_phone": organization.get("phone"),
            "company_founded_year": organization.get("founded_year"),
            "company_location": self._format_company_location(organization),
            # Metadata
            "apollo_id": person.get("id"),
            "enriched_at": datetime.utcnow(),
        }

    def _parse_organization_response(self, domain: str, org: dict) -> dict:
        """Parse Apollo organization response."""
        return {
            "domain": domain,
            "enriched": True,
            "name": org.get("name"),
            "industry": org.get("industry"),
            "estimated_num_employees": org.get("estimated_num_employees"),
            "linkedin_url": org.get("linkedin_url"),
            "phone": org.get("phone"),
            "founded_year": org.get("founded_year"),
            "city": org.get("city"),
            "state": org.get("state"),
            "country": org.get("country"),
            "logo_url": org.get("logo_url"),
            "apollo_id": org.get("id"),
            "enriched_at": datetime.utcnow(),
        }

    def _parse_employment_history(self, history: list) -> list[dict]:
        """Parse employment history from Apollo."""
        parsed = []
        for job in history[:5]:  # Limit to last 5 jobs
            parsed.append({
                "title": job.get("title"),
                "company_name": job.get("organization_name"),
                "start_date": job.get("start_date"),
                "end_date": job.get("end_date"),
                "is_current": job.get("current", False),
            })
        return parsed

    def _format_company_location(self, org: dict) -> Optional[str]:
        """Format company location string."""
        parts = []
        if org.get("city"):
            parts.append(org["city"])
        if org.get("state"):
            parts.append(org["state"])
        if org.get("country"):
            parts.append(org["country"])
        return ", ".join(parts) if parts else None

    def _empty_result(self, email: str) -> dict:
        """Return empty result for non-matched emails."""
        return {
            "email": email,
            "enriched": False,
            "enriched_at": datetime.utcnow(),
        }


# Singleton instance
_apollo_service: Optional[ApolloService] = None


def get_apollo_service() -> ApolloService:
    global _apollo_service
    if _apollo_service is None:
        _apollo_service = ApolloService()
    return _apollo_service
