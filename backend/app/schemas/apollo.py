from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class EmploymentHistory(BaseModel):
    title: Optional[str] = None
    company_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class ApolloEnrichRequest(BaseModel):
    email: EmailStr


class ApolloEnrichResponse(BaseModel):
    email: str
    enriched: bool
    # Personal info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    title: Optional[str] = None
    headline: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone_numbers: list[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    # Employment info
    employment_history: list[EmploymentHistory] = []
    seniority: Optional[str] = None
    departments: list[str] = []
    # Company info
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[int] = None
    company_linkedin_url: Optional[str] = None
    company_phone: Optional[str] = None
    company_founded_year: Optional[int] = None
    company_location: Optional[str] = None
    # Metadata
    apollo_id: Optional[str] = None
    enriched_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ApolloBulkEnrichRequest(BaseModel):
    emails: list[EmailStr]


class ApolloBulkEnrichResponse(BaseModel):
    results: list[ApolloEnrichResponse]
    total: int
    enriched_count: int
    not_found_count: int


class ApolloOrganizationRequest(BaseModel):
    domain: str


class ApolloOrganizationResponse(BaseModel):
    domain: str
    enriched: bool
    name: Optional[str] = None
    industry: Optional[str] = None
    estimated_num_employees: Optional[int] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    founded_year: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    apollo_id: Optional[str] = None
    enriched_at: Optional[datetime] = None

    class Config:
        from_attributes = True
