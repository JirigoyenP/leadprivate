"""
Progress router - real-time polling for batch/pipeline progress.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.batch import BatchJob
from app.tasks import celery_app

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/{batch_id}")
async def get_progress(batch_id: int, db: Session = Depends(get_db)):
    """Get real-time progress for a batch/pipeline operation."""
    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    response = {
        "batch_id": batch_id,
        "status": batch.status,
        "total": batch.total_emails,
        "processed": batch.processed_emails,
        "valid_count": batch.valid_count,
        "invalid_count": batch.invalid_count,
        "unknown_count": batch.unknown_count,
        "percent": (
            int((batch.processed_emails / batch.total_emails) * 100)
            if batch.total_emails > 0
            else 0
        ),
    }

    # Try to get Celery task metadata for more detail (phase info)
    # Look up active tasks for this batch
    inspect = celery_app.control.inspect()
    try:
        active = inspect.active() or {}
        for worker_tasks in active.values():
            for task in worker_tasks:
                task_args = task.get("args", [])
                if task_args and len(task_args) > 0 and task_args[0] == batch_id:
                    # Found the active task, try to get its state
                    result = celery_app.AsyncResult(task["id"])
                    if result.state == "PROGRESS" and result.info:
                        response["phase"] = result.info.get("phase")
                        response["current"] = result.info.get("current")
                        response["total"] = result.info.get("total", response["total"])
                        response["percent"] = result.info.get("percent", response["percent"])
                    break
    except Exception:
        # Celery inspect can fail in some environments; the basic batch data is still useful
        pass

    return response
