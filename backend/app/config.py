from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    debug: bool = False
    secret_key: str = "change-me-in-production"
    cors_origins: str = "http://localhost:5173"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/leadcleanse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ZeroBounce
    zerobounce_api_key: str = ""
    zerobounce_base_url: str = "https://api.zerobounce.net/v2"

    # HubSpot
    hubspot_client_id: str = ""
    hubspot_client_secret: str = ""
    hubspot_redirect_uri: str = "http://localhost:8000/api/hubspot/callback"

    # Apollo.io
    apollo_api_key: str = ""

    # LinkedIn Scraping
    linkedin_username: str = ""
    linkedin_password: str = ""
    linkedin_geckodriver_path: str = ""
    linkedin_scrape_schedule: str = "0 8 * * *"  # Daily at 8 AM (cron format)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
