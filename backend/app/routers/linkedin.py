from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.linkedin import LinkedInKeyword, LinkedInPost, LinkedInScrapeJob
from app.models.batch import BatchJob
from app.schemas.linkedin import (
    LinkedInKeywordCreate,
    LinkedInKeywordResponse,
    LinkedInKeywordList,
    LinkedInPostResponse,
    LinkedInPostList,
    LinkedInScrapeRequest,
    LinkedInScrapeJobResponse,
    LinkedInScrapeJobList,
    LinkedInProcessLeadsRequest,
    LinkedInProcessLeadsResponse,
)
from app.tasks.linkedin import scrape_linkedin_feed, search_linkedin_posts, process_linkedin_leads

router = APIRouter(prefix="/api/linkedin", tags=["linkedin"])


# Keywords endpoints
@router.get("/keywords", response_model=LinkedInKeywordList)
async def get_keywords(db: Session = Depends(get_db)):
    """Get all LinkedIn keywords."""
    keywords = db.query(LinkedInKeyword).all()
    return LinkedInKeywordList(
        keywords=[LinkedInKeywordResponse.model_validate(k) for k in keywords],
        total=len(keywords),
    )


@router.post("/keywords", response_model=LinkedInKeywordResponse)
async def add_keyword(
    keyword: LinkedInKeywordCreate,
    db: Session = Depends(get_db),
):
    """Add a new keyword for LinkedIn searching."""
    existing = db.query(LinkedInKeyword).filter(
        LinkedInKeyword.keyword == keyword.keyword
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return LinkedInKeywordResponse.model_validate(existing)
        raise HTTPException(status_code=400, detail="Keyword already exists")

    new_keyword = LinkedInKeyword(keyword=keyword.keyword)
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)

    return LinkedInKeywordResponse.model_validate(new_keyword)


@router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    """Deactivate a keyword."""
    keyword = db.query(LinkedInKeyword).filter(LinkedInKeyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    keyword.is_active = False
    db.commit()

    return {"message": "Keyword deactivated"}


# Scraping endpoints
@router.post("/scrape", response_model=LinkedInScrapeJobResponse)
async def start_scrape(
    request: LinkedInScrapeRequest,
    db: Session = Depends(get_db),
):
    """
    Start a LinkedIn scraping job.

    - search_type: 'feed' to scrape the feed, 'search' to search by keywords
    - keywords: Optional custom keywords (uses saved keywords if not provided)
    - max_scrolls: Number of scroll iterations (more = more posts but slower)
    """
    # Create scrape job
    job = LinkedInScrapeJob(
        search_type=request.search_type,
        status="pending",
        is_scheduled=False,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Queue the appropriate task
    if request.search_type == "search":
        search_linkedin_posts.delay(job.id, request.keywords, request.max_scrolls)
    else:
        scrape_linkedin_feed.delay(job.id, request.max_scrolls)

    return LinkedInScrapeJobResponse.model_validate(job)


@router.get("/scrape/{job_id}", response_model=LinkedInScrapeJobResponse)
async def get_scrape_job(job_id: int, db: Session = Depends(get_db)):
    """Get status of a scraping job."""
    job = db.query(LinkedInScrapeJob).filter(LinkedInScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return LinkedInScrapeJobResponse.model_validate(job)


@router.get("/scrape", response_model=LinkedInScrapeJobList)
async def get_scrape_jobs(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Get recent scraping jobs."""
    jobs = db.query(LinkedInScrapeJob).order_by(
        LinkedInScrapeJob.created_at.desc()
    ).limit(limit).all()

    return LinkedInScrapeJobList(
        jobs=[LinkedInScrapeJobResponse.model_validate(j) for j in jobs],
        total=len(jobs),
    )


# Posts endpoints
@router.get("/posts", response_model=LinkedInPostList)
async def get_posts(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    unprocessed_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Get scraped LinkedIn posts."""
    query = db.query(LinkedInPost)

    if unprocessed_only:
        query = query.filter(LinkedInPost.is_processed == False)

    total = query.count()
    unprocessed_count = db.query(LinkedInPost).filter(
        LinkedInPost.is_processed == False
    ).count()

    posts = query.order_by(
        LinkedInPost.scraped_at.desc()
    ).offset(offset).limit(limit).all()

    return LinkedInPostList(
        posts=[LinkedInPostResponse.model_validate(p) for p in posts],
        total=total,
        unprocessed_count=unprocessed_count,
    )


@router.get("/posts/{post_id}", response_model=LinkedInPostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post."""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return LinkedInPostResponse.model_validate(post)


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post."""
    post = db.query(LinkedInPost).filter(LinkedInPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted"}


# Lead processing endpoints
@router.post("/process-leads", response_model=LinkedInProcessLeadsResponse)
async def process_leads(
    request: LinkedInProcessLeadsRequest,
    db: Session = Depends(get_db),
):
    """
    Process LinkedIn posts as leads.

    Extracts author information and optionally enriches with Apollo.io data.
    """
    # Count posts to process
    query = db.query(LinkedInPost).filter(LinkedInPost.is_processed == False)
    if request.post_ids:
        query = query.filter(LinkedInPost.id.in_(request.post_ids))

    posts_count = query.count()

    if posts_count == 0:
        return LinkedInProcessLeadsResponse(
            batch_id=0,
            status="completed",
            leads_queued=0,
            message="No unprocessed posts to process",
        )

    # Create batch job
    batch = BatchJob(
        filename=f"linkedin_leads_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        status="pending",
        total_emails=posts_count,
        source="linkedin",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Queue processing task
    process_linkedin_leads.delay(
        batch.id,
        post_ids=request.post_ids,
        enrich_with_apollo=request.enrich_with_apollo,
    )

    return LinkedInProcessLeadsResponse(
        batch_id=batch.id,
        status="processing",
        leads_queued=posts_count,
        message=f"Processing {posts_count} LinkedIn leads",
    )


# Stats endpoint
@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get LinkedIn scraping statistics."""
    total_posts = db.query(LinkedInPost).count()
    unprocessed_posts = db.query(LinkedInPost).filter(
        LinkedInPost.is_processed == False
    ).count()
    processed_posts = total_posts - unprocessed_posts

    total_jobs = db.query(LinkedInScrapeJob).count()
    completed_jobs = db.query(LinkedInScrapeJob).filter(
        LinkedInScrapeJob.status == "completed"
    ).count()

    keywords_count = db.query(LinkedInKeyword).filter(
        LinkedInKeyword.is_active == True
    ).count()

    return {
        "posts": {
            "total": total_posts,
            "unprocessed": unprocessed_posts,
            "processed": processed_posts,
        },
        "jobs": {
            "total": total_jobs,
            "completed": completed_jobs,
        },
        "keywords_count": keywords_count,
    }
