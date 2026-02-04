import asyncio
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from app.tasks import celery_app
from app.database import SessionLocal
from app.models.batch import BatchJob
from app.services.verification import get_verification_service

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_csv_batch(self, batch_id: int):
    """
    Process a CSV batch job in the background.

    Args:
        batch_id: ID of the BatchJob to process
    """
    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        # Update status
        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        db.commit()

        # Read CSV
        df = pd.read_csv(batch.input_file_path)

        # Find email column
        email_column = None
        for col in df.columns:
            if "email" in col.lower():
                email_column = col
                break

        if not email_column:
            batch.status = "failed"
            batch.error_message = "No email column found in CSV"
            db.commit()
            return {"error": "No email column found"}

        emails = df[email_column].dropna().tolist()
        batch.total_emails = len(emails)
        db.commit()

        # Process emails
        service = get_verification_service(db)
        results = []

        for i, email in enumerate(emails):
            try:
                result = asyncio.run(
                    service.verify_email(str(email).strip(), batch_id=batch_id)
                )
                results.append(result)

                # Upsert lead record
                try:
                    from app.services.lead_manager import upsert_lead_from_verification
                    from app.models.email import EmailVerification
                    verification_record = (
                        db.query(EmailVerification)
                        .filter(EmailVerification.email == str(email).strip().lower())
                        .order_by(EmailVerification.created_at.desc())
                        .first()
                    )
                    if verification_record:
                        upsert_lead_from_verification(db, str(email).strip(), verification_record, source="csv")
                except Exception as lead_err:
                    logger.warning(f"Failed to upsert lead for {email}: {lead_err}")

                # Update progress
                batch.processed_emails = i + 1
                if result.get("status") == "valid":
                    batch.valid_count += 1
                elif result.get("status") == "invalid":
                    batch.invalid_count += 1
                else:
                    batch.unknown_count += 1
                db.commit()

                # Update Celery task state
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(emails),
                        "percent": int((i + 1) / len(emails) * 100),
                    },
                )

            except Exception as e:
                results.append({
                    "email": email,
                    "status": "error",
                    "error": str(e),
                })

        # Create output CSV
        output_df = df.copy()
        email_to_result = {r["email"]: r for r in results if "email" in r}

        output_df["verification_status"] = output_df[email_column].apply(
            lambda x: email_to_result.get(str(x).strip().lower(), {}).get("status", "unknown")
        )
        output_df["verification_sub_status"] = output_df[email_column].apply(
            lambda x: email_to_result.get(str(x).strip().lower(), {}).get("sub_status", "")
        )

        # Save output
        output_path = batch.input_file_path.replace(".csv", "_verified.csv")
        output_df.to_csv(output_path, index=False)

        # Update batch
        batch.status = "completed"
        batch.output_file_path = output_path
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "total": len(emails),
            "valid": batch.valid_count,
            "invalid": batch.invalid_count,
            "unknown": batch.unknown_count,
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


@celery_app.task(bind=True)
def process_hubspot_contacts(self, batch_id: int, contact_data: list[dict]):
    """
    Process HubSpot contacts for verification.

    Args:
        batch_id: ID of the BatchJob
        contact_data: List of contact dicts with id and email
    """
    db = SessionLocal()
    try:
        batch = db.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if not batch:
            return {"error": "Batch not found"}

        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        batch.total_emails = len(contact_data)
        db.commit()

        service = get_verification_service(db)
        results = []

        for i, contact in enumerate(contact_data):
            try:
                email = contact["email"]
                result = asyncio.run(
                    service.verify_email(email, batch_id=batch_id)
                )
                result["contact_id"] = contact["id"]
                results.append(result)

                # Upsert lead record
                try:
                    from app.services.lead_manager import upsert_lead_from_verification
                    from app.models.email import EmailVerification
                    verification_record = (
                        db.query(EmailVerification)
                        .filter(EmailVerification.email == email.lower().strip())
                        .order_by(EmailVerification.created_at.desc())
                        .first()
                    )
                    if verification_record:
                        upsert_lead_from_verification(db, email, verification_record, source="hubspot")
                except Exception as lead_err:
                    logger.warning(f"Failed to upsert lead for {email}: {lead_err}")

                batch.processed_emails = i + 1
                if result.get("status") == "valid":
                    batch.valid_count += 1
                elif result.get("status") == "invalid":
                    batch.invalid_count += 1
                else:
                    batch.unknown_count += 1
                db.commit()

                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(contact_data),
                        "percent": int((i + 1) / len(contact_data) * 100),
                    },
                )

            except Exception as e:
                results.append({
                    "contact_id": contact["id"],
                    "email": contact["email"],
                    "status": "error",
                    "error": str(e),
                })

        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db.commit()

        return {
            "batch_id": batch_id,
            "status": "completed",
            "results": results,
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
