"""
Instantly.ai API client for outreach automation.
"""

from __future__ import annotations

import httpx
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class InstantlyError(Exception):
    """Custom exception for Instantly API errors."""
    pass


class InstantlyService:
    """
    Instantly.ai API service for email outreach campaigns.
    """

    BASE_URL = "https://api.instantly.ai/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def test_connection(self) -> dict:
        """Test the API key by listing campaigns."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/campaign/list",
                    params={"api_key": self.api_key},
                )
                if response.status_code == 401:
                    return {"connected": False, "error": "Invalid API key"}
                if response.status_code != 200:
                    return {"connected": False, "error": f"HTTP {response.status_code}"}

                return {"connected": True}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def list_campaigns(self) -> list[dict]:
        """List all campaigns from Instantly."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/campaign/list",
                params={"api_key": self.api_key},
            )

            if response.status_code != 200:
                raise InstantlyError(f"Failed to list campaigns: HTTP {response.status_code}")

            data = response.json()
            # Instantly returns a list of campaign objects
            if isinstance(data, list):
                return data
            return data.get("campaigns", data.get("data", []))

    async def push_lead_to_campaign(
        self,
        campaign_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
        personalization: Optional[dict] = None,
    ) -> dict:
        """
        Add a lead to an Instantly campaign.

        Args:
            campaign_id: Instantly campaign ID
            email: Lead email
            first_name: Lead first name (personalization)
            last_name: Lead last name (personalization)
            company_name: Lead company name (personalization)
            personalization: Additional custom variables

        Returns:
            API response dict
        """
        lead_data: dict = {
            "email": email,
        }

        # Add personalization variables
        variables = {}
        if first_name:
            variables["first_name"] = first_name
            lead_data["first_name"] = first_name
        if last_name:
            variables["last_name"] = last_name
            lead_data["last_name"] = last_name
        if company_name:
            variables["company_name"] = company_name
            lead_data["company_name"] = company_name
        if personalization:
            variables.update(personalization)

        if variables:
            lead_data["variables"] = variables

        payload = {
            "api_key": self.api_key,
            "campaign_id": campaign_id,
            "skip_if_in_workspace": False,
            "leads": [lead_data],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/lead/add",
                json=payload,
            )

            if response.status_code != 200:
                raise InstantlyError(f"Failed to push lead: HTTP {response.status_code} - {response.text}")

            return response.json()

    async def push_leads_to_campaign(
        self,
        campaign_id: str,
        leads: list[dict],
    ) -> dict:
        """
        Add multiple leads to an Instantly campaign.

        Args:
            campaign_id: Instantly campaign ID
            leads: List of lead dicts with email, first_name, last_name, company_name, etc.

        Returns:
            API response dict
        """
        lead_data_list = []
        for lead in leads:
            lead_data: dict = {"email": lead["email"]}
            variables = {}

            for field in ["first_name", "last_name", "company_name", "title", "phone", "linkedin_url"]:
                if lead.get(field):
                    variables[field] = lead[field]
                    lead_data[field] = lead[field]

            if variables:
                lead_data["variables"] = variables

            lead_data_list.append(lead_data)

        payload = {
            "api_key": self.api_key,
            "campaign_id": campaign_id,
            "skip_if_in_workspace": False,
            "leads": lead_data_list,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/lead/add",
                json=payload,
            )

            if response.status_code != 200:
                raise InstantlyError(f"Failed to push leads: HTTP {response.status_code} - {response.text}")

            return response.json()
