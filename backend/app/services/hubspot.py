import httpx
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.hubspot_sync import HubSpotConnection


class HubSpotError(Exception):
    """Custom exception for HubSpot API errors."""
    pass


class HubSpotService:
    OAUTH_URL = "https://app.hubspot.com/oauth/authorize"
    TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    API_BASE = "https://api.hubapi.com"

    # Verification properties
    VERIFICATION_STATUS_PROPERTY = "email_verification_status"
    VERIFICATION_DATE_PROPERTY = "email_verification_date"

    # Apollo enrichment properties
    ENRICHMENT_JOB_TITLE_PROPERTY = "jobtitle"  # Built-in HubSpot property
    ENRICHMENT_COMPANY_PROPERTY = "company"  # Built-in HubSpot property
    ENRICHMENT_PHONE_PROPERTY = "phone"  # Built-in HubSpot property
    ENRICHMENT_LINKEDIN_PROPERTY = "linkedin_url"  # Custom property
    ENRICHMENT_SENIORITY_PROPERTY = "apollo_seniority"  # Custom property
    ENRICHMENT_COMPANY_SIZE_PROPERTY = "apollo_company_size"  # Custom property
    ENRICHMENT_COMPANY_INDUSTRY_PROPERTY = "apollo_company_industry"  # Custom property
    ENRICHMENT_DATE_PROPERTY = "apollo_enrichment_date"  # Custom property

    def __init__(self, db: Session):
        self.settings = get_settings()
        self.db = db
        self._connection: Optional[HubSpotConnection] = None

    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL."""
        scopes = [
            "crm.objects.contacts.read",
            "crm.objects.contacts.write",
            "crm.schemas.contacts.read",
            "crm.schemas.contacts.write",
        ]
        params = {
            "client_id": self.settings.hubspot_client_id,
            "redirect_uri": self.settings.hubspot_redirect_uri,
            "scope": " ".join(scopes),
        }
        if state:
            params["state"] = state

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.OAUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> HubSpotConnection:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.settings.hubspot_client_id,
                    "client_secret": self.settings.hubspot_client_secret,
                    "redirect_uri": self.settings.hubspot_redirect_uri,
                    "code": code,
                },
            )

            if response.status_code != 200:
                raise HubSpotError(f"Token exchange failed: {response.text}")

            data = response.json()

            # Deactivate existing connections
            self.db.query(HubSpotConnection).update({"is_active": False})

            # Create new connection
            connection = HubSpotConnection(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=data["expires_in"]),
                is_active=True,
            )
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)

            return connection

    async def refresh_token(self, connection: HubSpotConnection) -> HubSpotConnection:
        """Refresh an expired access token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.settings.hubspot_client_id,
                    "client_secret": self.settings.hubspot_client_secret,
                    "refresh_token": connection.refresh_token,
                },
            )

            if response.status_code != 200:
                raise HubSpotError(f"Token refresh failed: {response.text}")

            data = response.json()
            connection.access_token = data["access_token"]
            connection.refresh_token = data["refresh_token"]
            connection.expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
            self.db.commit()
            self.db.refresh(connection)

            return connection

    def get_active_connection(self) -> Optional[HubSpotConnection]:
        """Get the active HubSpot connection."""
        if self._connection:
            return self._connection

        self._connection = (
            self.db.query(HubSpotConnection)
            .filter(HubSpotConnection.is_active == True)
            .first()
        )
        return self._connection

    async def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        connection = self.get_active_connection()
        if not connection:
            raise HubSpotError("No active HubSpot connection")

        # Refresh if expired or about to expire (within 5 minutes)
        expires_at = connection.expires_at
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        if expires_at <= datetime.utcnow() + timedelta(minutes=5):
            connection = await self.refresh_token(connection)

        return connection.access_token

    async def get_contacts(
        self,
        limit: int = 100,
        after: Optional[str] = None,
        only_unverified: bool = False,
    ) -> dict:
        """Fetch contacts from HubSpot."""
        token = await self._get_access_token()

        properties = [
            "email",
            "firstname",
            "lastname",
            self.VERIFICATION_STATUS_PROPERTY,
            self.VERIFICATION_DATE_PROPERTY,
        ]

        params = {
            "limit": min(limit, 100),
            "properties": ",".join(properties),
        }
        if after:
            params["after"] = after

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.API_BASE}/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )

            if response.status_code != 200:
                raise HubSpotError(f"Failed to fetch contacts: {response.text}")

            data = response.json()

            contacts = []
            for result in data.get("results", []):
                props = result.get("properties", {})
                email = props.get("email")
                if not email:
                    continue

                # Filter unverified if requested
                if only_unverified:
                    status = props.get(self.VERIFICATION_STATUS_PROPERTY)
                    if status and status != "":
                        continue

                contacts.append({
                    "id": result["id"],
                    "email": email,
                    "firstname": props.get("firstname"),
                    "lastname": props.get("lastname"),
                    "email_verification_status": props.get(self.VERIFICATION_STATUS_PROPERTY),
                    "email_verification_date": props.get(self.VERIFICATION_DATE_PROPERTY),
                })

            paging = data.get("paging", {}).get("next", {})

            return {
                "contacts": contacts,
                "total": len(contacts),
                "has_more": "after" in paging,
                "next_cursor": paging.get("after"),
            }

    async def update_contact(
        self,
        contact_id: str,
        verification_status: str,
        verification_date: datetime,
    ) -> bool:
        """Update a contact with verification results."""
        token = await self._get_access_token()

        properties = {
            self.VERIFICATION_STATUS_PROPERTY: verification_status,
            self.VERIFICATION_DATE_PROPERTY: verification_date.isoformat(),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{self.API_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )

            return response.status_code == 200

    async def update_contact_enrichment(
        self,
        contact_id: str,
        enrichment_data: dict,
    ) -> bool:
        """Update a contact with Apollo enrichment data."""
        token = await self._get_access_token()

        properties = {}

        # Map enrichment data to HubSpot properties
        if enrichment_data.get("title"):
            properties[self.ENRICHMENT_JOB_TITLE_PROPERTY] = enrichment_data["title"]

        if enrichment_data.get("company_name"):
            properties[self.ENRICHMENT_COMPANY_PROPERTY] = enrichment_data["company_name"]

        # Use first phone number if available
        phone_numbers = enrichment_data.get("phone_numbers") or []
        if phone_numbers and len(phone_numbers) > 0:
            properties[self.ENRICHMENT_PHONE_PROPERTY] = phone_numbers[0]

        if enrichment_data.get("linkedin_url"):
            properties[self.ENRICHMENT_LINKEDIN_PROPERTY] = enrichment_data["linkedin_url"]

        if enrichment_data.get("seniority"):
            properties[self.ENRICHMENT_SENIORITY_PROPERTY] = enrichment_data["seniority"]

        if enrichment_data.get("company_size"):
            properties[self.ENRICHMENT_COMPANY_SIZE_PROPERTY] = str(enrichment_data["company_size"])

        if enrichment_data.get("company_industry"):
            properties[self.ENRICHMENT_COMPANY_INDUSTRY_PROPERTY] = enrichment_data["company_industry"]

        # Set enrichment date
        properties[self.ENRICHMENT_DATE_PROPERTY] = datetime.utcnow().isoformat()

        if not properties:
            return True  # Nothing to update

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{self.API_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )

            return response.status_code == 200

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact from HubSpot."""
        token = await self._get_access_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.API_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            return response.status_code == 204

    async def get_lists(self) -> list[dict]:
        """Fetch contact lists from HubSpot."""
        token = await self._get_access_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.API_BASE}/crm/v3/lists/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": "",
                    "additionalProperties": ["hs_list_size"],
                },
            )

            if response.status_code != 200:
                raise HubSpotError(f"Failed to fetch lists: {response.text}")

            data = response.json()
            lists = []
            for item in data.get("lists", []):
                if item.get("objectTypeId") != "0-1":
                    continue
                lists.append({
                    "id": item.get("listId"),
                    "name": item.get("name", ""),
                    "size": item.get("additionalProperties", {}).get("hs_list_size", 0),
                })

            return lists

    async def delete_contacts_batch(self, contact_ids: list[str]) -> dict:
        """Delete multiple contacts from HubSpot."""
        token = await self._get_access_token()

        deleted = []
        failed = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for contact_id in contact_ids:
                response = await client.delete(
                    f"{self.API_BASE}/crm/v3/objects/contacts/{contact_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 204:
                    deleted.append(contact_id)
                else:
                    failed.append({"id": contact_id, "error": response.text})

        return {"deleted": deleted, "failed": failed}

    async def create_contact(self, contact_data: dict) -> dict:
        """
        Create a new contact in HubSpot. Falls back to update if contact exists (409).

        Args:
            contact_data: Dictionary with contact properties (email, firstname, lastname, etc.)

        Returns:
            Dictionary with contact id and status
        """
        token = await self._get_access_token()

        properties = {"email": contact_data["email"]}

        if contact_data.get("first_name"):
            properties["firstname"] = contact_data["first_name"]
        if contact_data.get("last_name"):
            properties["lastname"] = contact_data["last_name"]
        if contact_data.get("title"):
            properties[self.ENRICHMENT_JOB_TITLE_PROPERTY] = contact_data["title"]
        if contact_data.get("company_name"):
            properties[self.ENRICHMENT_COMPANY_PROPERTY] = contact_data["company_name"]
        if contact_data.get("linkedin_url"):
            properties[self.ENRICHMENT_LINKEDIN_PROPERTY] = contact_data["linkedin_url"]
        if contact_data.get("seniority"):
            properties[self.ENRICHMENT_SENIORITY_PROPERTY] = contact_data["seniority"]
        if contact_data.get("company_size"):
            properties[self.ENRICHMENT_COMPANY_SIZE_PROPERTY] = str(contact_data["company_size"])
        if contact_data.get("company_industry"):
            properties[self.ENRICHMENT_COMPANY_INDUSTRY_PROPERTY] = contact_data["company_industry"]

        phone_numbers = contact_data.get("phone_numbers") or []
        if phone_numbers:
            properties[self.ENRICHMENT_PHONE_PROPERTY] = phone_numbers[0]

        properties[self.ENRICHMENT_DATE_PROPERTY] = datetime.utcnow().isoformat()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.API_BASE}/crm/v3/objects/contacts",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"properties": properties},
            )

            if response.status_code in (200, 201):
                data = response.json()
                return {"id": data["id"], "status": "created"}

            if response.status_code == 409:
                # Contact already exists — extract existing ID and update
                conflict_data = response.json()
                existing_id = None
                message = conflict_data.get("message", "")
                # HubSpot 409 message contains "Existing ID: <id>"
                if "Existing ID:" in message:
                    existing_id = message.split("Existing ID:")[-1].strip().rstrip(".")

                if existing_id:
                    update_resp = await client.patch(
                        f"{self.API_BASE}/crm/v3/objects/contacts/{existing_id}",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        json={"properties": properties},
                    )
                    if update_resp.status_code == 200:
                        return {"id": existing_id, "status": "updated"}

                return {"id": existing_id, "status": "conflict", "error": message}

            raise HubSpotError(f"Failed to create contact: {response.text}")

    async def ensure_properties_exist(self) -> bool:
        """Ensure custom properties exist in HubSpot."""
        token = await self._get_access_token()

        properties_to_create = [
            # Verification properties
            {
                "name": self.VERIFICATION_STATUS_PROPERTY,
                "label": "Email Verification Status",
                "type": "enumeration",
                "fieldType": "select",
                "groupName": "contactinformation",
                "options": [
                    {"label": "Valid", "value": "valid"},
                    {"label": "Invalid", "value": "invalid"},
                    {"label": "Catch-All", "value": "catch-all"},
                    {"label": "Unknown", "value": "unknown"},
                ],
            },
            {
                "name": self.VERIFICATION_DATE_PROPERTY,
                "label": "Email Verification Date",
                "type": "datetime",
                "fieldType": "date",
                "groupName": "contactinformation",
            },
            # Apollo enrichment properties (custom ones - built-in ones like jobtitle, company, phone already exist)
            {
                "name": self.ENRICHMENT_LINKEDIN_PROPERTY,
                "label": "LinkedIn URL",
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
            },
            {
                "name": self.ENRICHMENT_SENIORITY_PROPERTY,
                "label": "Seniority Level",
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
            },
            {
                "name": self.ENRICHMENT_COMPANY_SIZE_PROPERTY,
                "label": "Company Size",
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
            },
            {
                "name": self.ENRICHMENT_COMPANY_INDUSTRY_PROPERTY,
                "label": "Company Industry",
                "type": "string",
                "fieldType": "text",
                "groupName": "contactinformation",
            },
            {
                "name": self.ENRICHMENT_DATE_PROPERTY,
                "label": "Apollo Enrichment Date",
                "type": "datetime",
                "fieldType": "date",
                "groupName": "contactinformation",
            },
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for prop in properties_to_create:
                # Check if property exists
                response = await client.get(
                    f"{self.API_BASE}/crm/v3/properties/contacts/{prop['name']}",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code == 404:
                    # Create property
                    create_response = await client.post(
                        f"{self.API_BASE}/crm/v3/properties/contacts",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                        json=prop,
                    )
                    if create_response.status_code not in (200, 201):
                        raise HubSpotError(f"Failed to create property: {create_response.text}")

        return True


def get_hubspot_service(db: Session) -> HubSpotService:
    return HubSpotService(db)
