import os
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.batch import BatchJob
from app.schemas.batch import BatchJobResponse, BatchJobStatus
from app.tasks.verification import process_csv_batch

router = APIRouter(prefix="/api/batch", tags=["batch"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=BatchJobResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file for batch email verification.

    The CSV must contain a column with 'email' in its name.
    Processing happens in the background.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create batch job
    batch = BatchJob(
        filename=file.filename,
        status="pending",
        input_file_path=str(file_path),
        source="csv",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Queue processing task
    process_csv_batch.delay(batch.id)

    return BatchJobResponse(
        id=batch.id,
        filename=batch.filename,
        status=batch.status,
        message="File uploaded. Processing started.",
    )


@router.get("/{batch_id}", response_model=BatchJobStatus)
async def get_batch_status(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """Get the status of a batch job."""
    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    progress = 0
    if batch.total_emails > 0:
        progress = (batch.processed_emails / batch.total_emails) * 100

    return BatchJobStatus(
        id=batch.id,
        filename=batch.filename,
        status=batch.status,
        total_emails=batch.total_emails,
        processed_emails=batch.processed_emails,
        valid_count=batch.valid_count,
        invalid_count=batch.invalid_count,
        unknown_count=batch.unknown_count,
        progress_percent=progress,
        error_message=batch.error_message,
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
    )


@router.get("/{batch_id}/download")
async def download_results(
    batch_id: int,
    db: Session = Depends(get_db),
):
    """Download the verified results CSV."""
    batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="Batch not yet completed")

    if not batch.output_file_path or not os.path.exists(batch.output_file_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        batch.output_file_path,
        media_type="text/csv",
        filename=f"verified_{batch.filename}",
    )


@router.get("/", response_model=list[BatchJobStatus])
async def list_batches(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all batch jobs."""
    batches = (
        db.query(BatchJob)
        .order_by(BatchJob.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for batch in batches:
        progress = 0
        if batch.total_emails > 0:
            progress = (batch.processed_emails / batch.total_emails) * 100

        results.append(
            BatchJobStatus(
                id=batch.id,
                filename=batch.filename,
                status=batch.status,
                total_emails=batch.total_emails,
                processed_emails=batch.processed_emails,
                valid_count=batch.valid_count,
                invalid_count=batch.invalid_count,
                unknown_count=batch.unknown_count,
                progress_percent=progress,
                error_message=batch.error_message,
                created_at=batch.created_at,
                started_at=batch.started_at,
                completed_at=batch.completed_at,
            )
        )

    return results
