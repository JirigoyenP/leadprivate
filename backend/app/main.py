from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base
from app.routers import verify_router, batch_router, hubspot_router, apollo_router, linkedin_router, dashboard_router, leads_router, progress_router, outreach_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title="EbomboLeadManager",
    description="Email verification platform with HubSpot and ZeroBounce integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(verify_router)
app.include_router(batch_router)
app.include_router(hubspot_router)
app.include_router(apollo_router)
app.include_router(linkedin_router)
app.include_router(dashboard_router)
app.include_router(leads_router)
app.include_router(progress_router)
app.include_router(outreach_router)


@app.get("/")
async def root():
    return {
        "name": "EbomboLeadManager",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
