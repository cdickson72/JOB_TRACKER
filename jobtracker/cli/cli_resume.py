import typer
from typing import Optional
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich import box
from jobtracker.db import get_db
from jobtracker.models import Resume
from jobtracker.schemas import ResumeCreate
from pydantic import ValidationError

console = Console()
resume_app = typer.Typer(help="Manage resumes: add, list, update, remove")

# use centralized `get_db` contextmanager


# -----------------------------
# Resume Commands
# -----------------------------
@resume_app.command("add")
def add_resume(
    name: str = typer.Option(..., prompt=True),
    file_path: str = typer.Option(..., prompt=True),
    tags: Optional[str] = typer.Option(None, prompt=True),
):
    """Add a resume to the catalog"""
    # Validate input early using Pydantic schema
    try:
        ResumeCreate(name=name, file_path=file_path, tags=tags)
    except ValidationError as exc:
        console.print(f"[red]Invalid input:[/red] {exc}")
        raise typer.Exit(code=1)

    with get_db() as db:
        resume = Resume(name=name, file_path=file_path, tags=tags, created_at=datetime.now(timezone.utc))
        try:
            db.add(resume)
            db.commit()
            db.refresh(resume)
        except Exception:
            db.rollback()
            raise

        console.print(f"Added resume [bold]{resume.name}[/bold]")
        console.print(f"ID: {resume.id}")


@resume_app.command("list")
def list_resumes():
    """List available resumes"""
    with get_db() as db:
        resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    if not resumes:
        console.print("No resumes found.")
        return

    table = Table(title="Resumes", box=box.SQUARE, show_lines=True, header_style="bold cyan")
    table.add_column("ID", no_wrap=True)
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("File Path")
    table.add_column("Created (UTC)")

    for r in resumes:
        table.add_row(r.id, r.name, r.tags or "-", r.file_path, r.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    console.print(table)


@resume_app.command("update")
def update_resume(
    resume_id: str = typer.Argument(...),
    name: Optional[str] = typer.Option(None),
    tags: Optional[str] = typer.Option(None),
    file_path: Optional[str] = typer.Option(None),
):
    """Update fields on an existing resume"""
    with get_db() as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            console.print(f"Resume ID {resume_id} not found")
            raise typer.Exit()

        updated = False
        if name is not None:
            resume.name = name
            updated = True
        if tags is not None:
            resume.tags = tags
            updated = True
        if file_path is not None:
            # Validate file_path
            try:
                ResumeCreate(name=resume.name, file_path=file_path, tags=resume.tags)
            except ValidationError as exc:
                console.print(f"[red]Invalid file_path:[/red] {exc}")
                raise typer.Exit(code=1)
            resume.file_path = file_path
            updated = True

        if not updated:
            console.print("No fields provided to update")
            raise typer.Exit()
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        console.print(f"Updated resume [bold]{resume.name}[/bold]")


@resume_app.command("remove")
def remove_resume(resume_id: str = typer.Argument(...)):
    """Remove a resume if it is not associated with any jobs"""
    with get_db() as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            console.print(f"Resume ID {resume_id} not found")
            raise typer.Exit()
        if resume.jobs:
            console.print(f"Cannot remove resume [bold]{resume.name}[/bold] (used by {len(resume.jobs)} job(s))")
            raise typer.Exit()
        try:
            db.delete(resume)
            db.commit()
        except Exception:
            db.rollback()
            raise
        console.print(f"Removed resume [bold]{resume.name}[/bold]")
