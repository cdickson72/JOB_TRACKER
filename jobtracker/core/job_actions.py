# jobtracker/core/job_actions.py
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from pydantic import ValidationError
from jobtracker.models import Job, Resume, CoverLetter
from jobtracker.enums import JobStatus
from jobtracker.schemas import JobCreate, JobUpdate


# ------------------------------------------------------------------
# CREATE
# ------------------------------------------------------------------
def create_job(
    db: Session,
    company: str,
    title: str,
    source: Optional[str] = None,
    job_url: Optional[str] = None,
    location: Optional[str] = None,
    salary_range: Optional[str] = None,
    applied_date: Optional[datetime] = None,
    resume_id: Optional[str] = None,
    cover_letter_id: Optional[str] = None,
) -> Job:
    """Create and commit a new job to the database."""
    now = datetime.now(timezone.utc)
    applied_dt = applied_date or now

    try:
        job_in = JobCreate(
            company=company,
            title=title,
            location=location,
            salary_range=salary_range,
            job_url=job_url,
            source=source,
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid job data: {exc}")

    job = Job(
        company=job_in.company,
        title=job_in.title,
        source=job_in.source,
        job_url=str(job_in.job_url) if job_in.job_url else (job_url or None),
        location=job_in.location,
        salary_range=job_in.salary_range,
        status=JobStatus.APPLIED.value,
        applied_date=applied_dt,
        last_updated=now,
        created_at=now,
        resume_id=resume_id,
        cover_letter_id=cover_letter_id,
    )

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return job


# ------------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------------
def update_job(
    db: Session,
    job: Job,
    company: Optional[str] = None,
    title: Optional[str] = None,
    source: Optional[str] = None,
    job_url: Optional[str] = None,
    location: Optional[str] = None,
    salary_range: Optional[str] = None,
    applied_date: Optional[datetime] = None,
    resume_id: Optional[str] = None,
    cover_letter_id: Optional[str] = None,
) -> Job:
    """Update fields on an existing job and commit changes."""
    if company is not None:
        job.company = company
    if title is not None:
        job.title = title
    if source is not None:
        job.source = source
    if job_url is not None:
        job.job_url = str(job_url)
    if location is not None:
        job.location = location
    if salary_range is not None:
        job.salary_range = salary_range
    if applied_date is not None:
        job.applied_date = applied_date
    if resume_id is not None:
        job.resume_id = resume_id
    if cover_letter_id is not None:
        job.cover_letter_id = cover_letter_id

    try:
        job_up = JobUpdate(
            company=job.company,
            title=job.title,
            location=job.location,
            salary_range=job.salary_range,
            job_url=job.job_url,
            source=job.source,
        )
    except ValidationError as exc:
        raise ValueError(f"Invalid update data: {exc}")

    if job_up.salary_range is not None:
        job.salary_range = job_up.salary_range
    if job_up.job_url is not None:
        job.job_url = str(job_up.job_url)

    job.last_updated = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

    return job


# ------------------------------------------------------------------
# READ
# ------------------------------------------------------------------
def list_jobs(db: Session) -> List[Job]:
    """Return all jobs with Resume and CoverLetter eagerly loaded."""
    return (
        db.query(Job)
        .options(
            joinedload(Job.resume),
            joinedload(Job.cover_letter),
        )
        .order_by(Job.created_at.desc())
        .all()
    )


def get_job_by_id(db: Session, job_id: str) -> Optional[Job]:
    """Fetch a single job by ID."""
    return db.query(Job).filter(Job.id == job_id).first()


# ------------------------------------------------------------------
# DELETE
# ------------------------------------------------------------------
def delete_job(db: Session, job_id: str) -> Optional[Job]:
    """Delete a job by ID. Returns the deleted job or None."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return None

    try:
        db.delete(job)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return job

