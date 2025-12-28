import typer
from typing import Optional
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich import box
from jobtracker.db import get_db
from sqlalchemy.orm import joinedload
from jobtracker.models import Job, Resume, CoverLetter
from jobtracker.enums import JobStatus

console = Console()
job_app = typer.Typer(help="Manage tracked job applications: add, list, update, status, note, remove")

# use `get_db` contextmanager from `jobtracker.db`


# -----------------------------
# Add Job
# -----------------------------
def _parse_applied_date(applied_date: Optional[str], now: datetime) -> Optional[datetime]:
    """Parse an applied date string (YYYY-MM-DD) or return `now` when not provided.

    If parsing fails, prints a warning and returns `now`.
    """
    if not applied_date:
        return now
    try:
        return datetime.strptime(applied_date.strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        console.print("[red]Invalid applied date format; using current time instead.[/red]")
        return now


def _select_resume_id(db) -> Optional[str]:
    """Prompt the user to select a resume ID from available resumes, or return None."""
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    if not resumes:
        return None
    console.print("\nAvailable Resumes:")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    for r in resumes:
        table.add_row(r.id, r.name.replace("\n", " ").strip())
    console.print(table)
    selected = typer.prompt("Enter resume ID to attach", default="")
    return selected or None


def _select_cover_letter_id(db) -> Optional[str]:
    """Prompt the user to select a cover letter ID from available letters, or return None."""
    letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()
    if not letters:
        return None
    console.print("\nAvailable Cover Letters:")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    for cl in letters:
        table.add_row(cl.id, cl.name.replace("\n", " ").strip())
    console.print(table)
    selected = typer.prompt("Enter cover letter ID to attach", default="")
    return selected or None


def _create_and_commit_job(db, job: Job) -> Job:
    """Add, commit, and refresh a job instance in the database."""
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    except Exception:
        db.rollback()
        raise


def _print_added_job_details(db, job: Job, resume_id: Optional[str], cover_letter_id: Optional[str]) -> None:
    console.print(f"\nAdded job [bold]{job.company} — {job.title}[/bold]")
    if resume_id:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        console.print(f"   Resume attached: {resume.name if resume else resume_id}")
    if cover_letter_id:
        cl = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
        console.print(f"   Cover Letter attached: {cl.name if cl else cover_letter_id}")
    console.print(f"ID: {job.id}")


def _commit_job(db, job: Job) -> None:
    """Commit changes to a job and refresh from the database."""
    try:
        db.commit()
        db.refresh(job)
    except Exception:
        db.rollback()
        raise

@job_app.command("add")
def add_job(
    company: str = typer.Option(..., prompt=True),
    title: str = typer.Option(..., prompt=True),
    source: Optional[str] = typer.Option(None, prompt=True),
    job_url: Optional[str] = typer.Option(None, prompt=True),
    location: Optional[str] = typer.Option(None, prompt=True),
    salary_range: Optional[str] = typer.Option(None, prompt=True),
    applied_date: Optional[str] = typer.Option(None, help="Applied date in YYYY-MM-DD format"),
    resume_id: Optional[str] = typer.Option(None, help="Optional resume ID"),
    cover_letter_id: Optional[str] = typer.Option(None, help="Optional cover letter ID"),
):
    """Add a new job application"""
    now = datetime.now(timezone.utc)
    with get_db() as db:
        applied_dt = _parse_applied_date(applied_date, now)

        if not resume_id:
            resume_id = _select_resume_id(db)

        if not cover_letter_id:
            cover_letter_id = _select_cover_letter_id(db)

        # -----------------------------
        # Create Job
        # -----------------------------
        job = Job(
            company=company,
            title=title,
            source=source,
            job_url=job_url,
            location=location,
            salary_range=salary_range,
            status=JobStatus.APPLIED.value,
            applied_date=applied_dt,
            last_updated=now,
            created_at=now,
            resume_id=resume_id,
            cover_letter_id=cover_letter_id,
        )

        _create_and_commit_job(db, job)
        _print_added_job_details(db, job, resume_id, cover_letter_id)


@job_app.command("update")
def update_job(job_id: str = typer.Argument(..., help="ID of the job to update")):
    """Update fields on an existing job"""
    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            console.print(f"[red]Job ID {job_id} not found[/red]")
            raise typer.Exit()

        console.print(f"Updating job: [bold]{job.company} — {job.title}[/bold]\nPress Enter to keep current value.\n")

        # Update basic fields
        _prompt_update_basic_fields(job)

        # Update Resume
        _prompt_update_resume(db, job)

        # Update Cover Letter
        _prompt_update_cover_letter(db, job)

        job.last_updated = datetime.now(timezone.utc)
        _commit_job(db, job)

        console.print(f"\nUpdated job [bold]{job.company} — {job.title}[/bold]")
        if job.resume:
            console.print(f"   Resume attached: {job.resume.name}")
        if job.cover_letter:
            console.print(f"   Cover Letter attached: {job.cover_letter.name}")
        console.print(f"ID: {job.id}")


@job_app.command("list")
def list_jobs():
    """List all tracked job applications"""
    with get_db() as db:
        # Eager-load related Resume and CoverLetter so we can access their
        # attributes after the session is closed.
        jobs = (
            db.query(Job)
            .options(joinedload(Job.resume), joinedload(Job.cover_letter))
            .order_by(Job.created_at.desc())
            .all()
        )

    if not jobs:
        console.print("No jobs tracked yet.")
        return

    table = Table(title="Tracked Job Applications", box=box.SQUARE, show_lines=True, header_style="bold cyan")

    table.add_column("ID", no_wrap=True)
    table.add_column("Company")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Source")
    table.add_column("Applied (UTC)")
    table.add_column("Resume")
    table.add_column("Cover Letter")
    table.add_column("Salary Range")
    table.add_column("Location")
    table.add_column("URL")

    for job in jobs:
        table.add_row(
            job.id,
            job.company,
            job.title,
            job.status,
            job.source or "-",
            job.applied_date.strftime("%Y-%m-%d") if job.applied_date else "-",
            job.resume.name if job.resume else "-",
            job.cover_letter.name if job.cover_letter else "-",
            job.salary_range or "-",
            job.location or "-",
            job.job_url or "-",
        )

    # Print the table once after all rows are added
    console.print(table)


def _prompt_update_basic_fields(job: Job) -> None:
    """Prompt to update basic job fields in-place."""
    job.company = typer.prompt("Company", default=job.company)
    job.title = typer.prompt("Title", default=job.title)
    job.source = typer.prompt("Source", default=job.source or "")
    job.job_url = typer.prompt("Job URL", default=job.job_url or "")
    job.location = typer.prompt("Location", default=job.location or "")
    job.salary_range = typer.prompt("Salary Range", default=job.salary_range or "")

    applied_default = job.applied_date.strftime("%Y-%m-%d") if job.applied_date else ""
    applied_input = typer.prompt("Applied Date (YYYY-MM-DD)", default=applied_default)
    if applied_input.strip():
        try:
            job.applied_date = datetime.strptime(applied_input.strip(), "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            console.print("[red]Invalid date format. Keeping current value.[/red]")


def _prompt_update_resume(db, job: Job) -> None:
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    if not resumes:
        return
    console.print("\nAvailable Resumes:")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    for r in resumes:
        table.add_row(r.id, r.name.replace("\n", " ").strip())
    console.print(table)
    resume_default = job.resume_id if job.resume else ""
    resume_selected = typer.prompt("Enter resume ID to attach", default=resume_default)
    job.resume_id = resume_selected if resume_selected else job.resume_id


def _prompt_update_cover_letter(db, job: Job) -> None:
    letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()
    if not letters:
        return
    console.print("\nAvailable Cover Letters:")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    for cl in letters:
        table.add_row(cl.id, cl.name.replace("\n", " ").strip())
    console.print(table)
    cover_default = job.cover_letter_id if job.cover_letter else ""
    cover_selected = typer.prompt("Enter cover letter ID to attach", default=cover_default)
    job.cover_letter_id = cover_selected if cover_selected else job.cover_letter_id
@job_app.command("remove")
def remove_job(job_id: str = typer.Argument(...)):
    """Remove a job from tracking"""
    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            console.print(f"Job ID {job_id} not found")
            raise typer.Exit()
        try:
            db.delete(job)
            db.commit()
        except Exception:
            db.rollback()
            raise
        console.print(f"Removed job [bold]{job.company} — {job.title}[/bold]")


@job_app.command("status")
def update_job_status(job_id: str = typer.Argument(...), new_status: JobStatus = typer.Argument(...)):
    """Update the status of a job"""
    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            console.print(f"Job ID {job_id} not found")
            raise typer.Exit()

        job.status = new_status.value
        job.last_updated = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        msg = f"Updated status for [bold]{job.company} — {job.title}[/bold] to " f"[green]{new_status.value}[/green]"
        console.print(msg)
