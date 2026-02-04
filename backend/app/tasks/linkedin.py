"""
Celery tasks for LinkedIn scraping.
"""

import logging
from datetime import datetime
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.linkedin import LinkedInScrapeJob, LinkedInPost
from app.models.batch import BatchJob
from app.services.linkedin import get_linkedin_service, LinkedInError

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def scrape_linkedin_feed(self, job_id: int, max_scrolls: int = 10):
    """
    Scrape LinkedIn feed for posts matching keywords.

    Args:
        job_id: ID of the LinkedInScrapeJob
        max_scrolls: Maximum scroll iterations
    """
    db = SessionLocal()
    try:
        service = get_linkedin_service(db, headless=True)
        result = service.scrape_feed(job_id, max_scrolls)

        self.update_state(
            state="SUCCESS",
            meta=result,
        )

        return result

    except LinkedInError as e:
        return {"error": str(e), "job_id": job_id}

    except Exception as e:
        job = db.query(LinkedInScrapeJob).filter(LinkedInScrapeJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        return {"error": str(e), "job_id": job_id}

    finally:
        db.close()


@celery_app.task(bind=True)
def search_linkedin_posts(self, job_id: int, keywords: list[str] = None, max_scrolls: int = 5):
    """
    Search LinkedIn for posts matching specific keywords.

    Args:
        job_id: ID of the LinkedInScrapeJob
        keywords: Keywords to search
        max_scrolls: Scrolls per keyword
    """
    db = SessionLocal()
    try:
        service = get_linkedin_service(db, headless=True)
        result = service.search_posts(job_id, keywords, max_scrolls)

        self.update_state(
            state="SUCCESS",
            meta=result,
        )

        return result

    except LinkedInError as e:
        return {"error": str(e), "job_id": job_id}

    except Exception as e:
        job = db.query(LinkedInScrapeJob).filter(LinkedInScrapeJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        return {"error": str(e), "job_id": job_id}

    finally:
        db.close()


@celery_app.task(bind=True)
def process_linkedin_leads(
    self,
    batch_id: int,
    post_ids: list[int] = None,
    enrich_with_apollo: bool = True,
):
    """
    Process LinkedIn posts as leads - enrich with Apollo.io.

    Args:
        batch_id: ID of the BatchJob for tracking
        post_ids: Specific post IDs to process (None = all unprocessed)
        enrich_with_apollo: Whether to enrich with Apollo data
    """
    import asyncio
    from app.services.apollo import get_apollo_service
    from app.models.enrichment import ContactEnrichment

    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        db.commit()

        # Get posts to process
        query = db.query(LinkedInPost).filter(LinkedInPost.is_processed == False)
        if post_ids:
            query = query.filter(LinkedInPost.id.in_(post_ids))

        posts = query.all()
        batch.total_emails = len(posts)
        db.commit()

        if not enrich_with_apollo:
            # Just mark as processed
            for post in posts:
                post.is_processed = True
                post.enrichment_batch_id = batch_id
            db.commit()

            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            batch.processed_emails = len(posts)
            db.commit()

            return {
                "batch_id": batch_id,
                "status": "completed",
                "posts_processed": len(posts),
                "enriched": False,
            }

        # Enrich with Apollo
        apollo_service = get_apollo_service()
        enriched_count = 0
        error_count = 0

        for i, post in enumerate(posts):
            # Extract domain from profile URL to search for email
            # Apollo needs an email or domain, so we'll use the profile URL
            # to try to find the person

            try:
                # For now, we'll store the profile info for manual enrichment
                # Apollo's person match API typically needs email

                # Create enrichment record with what we have
                enrichment = ContactEnrichment(
                    email=f"linkedin_{post.id}@pending.local",  # Placeholder
                    enriched=False,
                    first_name=post.author_name.split()[0] if post.author_name else None,
                    last_name=" ".join(post.author_name.split()[1:]) if post.author_name and len(post.author_name.split()) > 1 else None,
                    full_name=post.author_name,
                    linkedin_url=post.author_profile_url,
                    city=post.author_country,
                    batch_id=batch_id,
                )
                db.add(enrichment)
                db.flush()
                db.refresh(enrichment)

                # Upsert lead record
                try:
                    from app.services.lead_manager import upsert_lead_from_enrichment
                    upsert_lead_from_enrichment(db, enrichment.email, enrichment, source="linkedin")
                except Exception as lead_err:
                    logger.warning(f"Failed to upsert lead from linkedin enrichment: {lead_err}")

                post.is_processed = True
                post.enrichment_batch_id = batch_id
                enriched_count += 1

            except Exception as e:
                error_count += 1

            batch.processed_emails = i + 1
            db.commit()

            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(posts),
                    "percent": int((i + 1) / len(posts) * 100),
                    "enriched": enriched_count,
                },
            )

        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "posts_processed": len(posts),
            "enriched": enriched_count,
            "errors": error_count,
        }

    except Exception as e:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch:
            batch.status = "failed"
            batch.error_message = str(e)
            db.commit()
        return {"error": str(e)}

    finally:
        db.close()


@celery_app.task
def scheduled_linkedin_scrape():
    """
    Scheduled task to scrape LinkedIn automatically.
    Called by Celery beat based on LINKEDIN_SCRAPE_SCHEDULE.
    """
    db = SessionLocal()
    try:
        # Create a new scrape job
        job = LinkedInScrapeJob(
            search_type="feed",
            status="pending",
            is_scheduled=True,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Trigger the scrape
        scrape_linkedin_feed.delay(job.id, max_scrolls=10)

        return {"message": "Scheduled scrape started", "job_id": job.id}

    finally:
        db.close()
