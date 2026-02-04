from pydantic import BaseModel
from typing import Optional


class ApolloSearchCriteria(BaseModel):
    person_titles: list[str] = []
    q_organization_domains: list[str] = []
    person_locations: list[str] = []
    person_seniorities: list[str] = []
    max_results: int = 25


class OneClickPipelineRequest(BaseModel):
    search_criteria: ApolloSearchCriteria


class OneClickPipelineResponse(BaseModel):
    batch_id: int
    status: str
    message: str


class PipelineContact(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    linkedin_url: Optional[str] = None
    seniority: Optional[str] = None


class PreviewSearchResponse(BaseModel):
    contacts: list[PipelineContact]
    total_available: int
    showing: int


class PipelineResultContact(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    verification_status: Optional[str] = None
    hubspot_status: Optional[str] = None


class PipelineResults(BaseModel):
    batch_id: int
    status: str
    search: dict = {}
    verification: dict = {}
    hubspot: dict = {}
    contacts: list[PipelineResultContact] = []
