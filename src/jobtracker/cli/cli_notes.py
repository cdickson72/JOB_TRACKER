from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table
from jobtracker.db import get_db
from jobtracker.models import Job, Note

console = Console()
note_app = typer.Typer(help="Manage job notes")


@note_app.command("add")
def add_note(
    job_id: str = typer.Argument(..., help="Job ID to attach the note to"),
    content: list[str] = typer.Argument(..., help="Note content"),
):
    """Add a note to a job"""
    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            console.print(f"[red]Job ID {job_id} not found[/red]")
            raise typer.Exit(1)

        note_text = " ".join(content)

        note = Note(
            job_id=job.id,
            content=note_text,
            created_at=datetime.now(timezone.utc),
        )

        try:
            db.add(note)
            db.commit()
        except Exception:
            db.rollback()
            raise

        console.print("[green]Note added successfully[/green]")


@note_app.command("list")
def list_notes(
    job_id: str = typer.Argument(..., help="Job ID to list notes for"),
):
    """List notes for a job"""

    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            console.print(f"[red]Job ID {job_id} not found[/red]")
            raise typer.Exit(1)

        if not job.notes:
            console.print("No notes found for this job.")
            return

        table = Table(title=f"Notes — {job.company} / {job.title}", show_lines=True)
        table.add_column("Created (UTC)", style="cyan", no_wrap=True)
        table.add_column("Note")

        for note in sorted(job.notes, key=lambda n: n.created_at):
            table.add_row(
                note.created_at.strftime("%Y-%m-%d %H:%M"),
                note.content,
            )

        console.print(table)
