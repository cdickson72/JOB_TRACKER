import typer
from typing import Optional
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich import box
from jobtracker.db import get_db
from jobtracker.models import CoverLetter

console = Console()
cover_letter_app = typer.Typer(help="Manage cover letters: add, list, update, remove")

# use centralized `get_db` contextmanager


# -----------------------------
# Cover Letter Commands
# -----------------------------
@cover_letter_app.command("add")
def add_cover_letter(
    name: str = typer.Option(..., prompt=True),
    file_path: str = typer.Option(..., prompt=True),
    tags: Optional[str] = typer.Option(None, prompt=True),
):
    """Add a cover letter to the catalog"""
    with get_db() as db:
        cl = CoverLetter(name=name, file_path=file_path, tags=tags, created_at=datetime.now(timezone.utc))
        try:
            db.add(cl)
            db.commit()
            db.refresh(cl)
        except Exception:
            db.rollback()
            raise

        console.print(f"Added cover letter [bold]{cl.name}[/bold]")
        console.print(f"ID: {cl.id}")


@cover_letter_app.command("list")
def list_cover_letters():
    """List available cover letters"""
    with get_db() as db:
        letters = db.query(CoverLetter).order_by(CoverLetter.created_at.desc()).all()
        if not letters:
            console.print("No cover letters found.")
            return
    table = Table(title="Cover Letters", box=box.SQUARE, show_lines=True, header_style="bold cyan")
    table.add_column("ID", no_wrap=True)
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("File Path")
    table.add_column("Created (UTC)")
    for cl in letters:
        table.add_row(cl.id, cl.name, cl.tags or "-", cl.file_path, cl.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    console.print(table)


@cover_letter_app.command("update")
def update_cover_letter(
    cover_letter_id: str = typer.Argument(...),
    name: Optional[str] = typer.Option(None),
    tags: Optional[str] = typer.Option(None),
    file_path: Optional[str] = typer.Option(None),
):
    """Update fields on an existing cover letter"""
    with get_db() as db:
        cl = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
        if not cl:
            console.print(f"Cover letter ID {cover_letter_id} not found")
            raise typer.Exit()
        updated = False
        if name is not None:
            cl.name = name
            updated = True
        if tags is not None:
            cl.tags = tags
            updated = True
        if file_path is not None:
            cl.file_path = file_path
            updated = True
        if not updated:
            console.print("No fields provided to update")
            raise typer.Exit()
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        console.print(f"Updated cover letter [bold]{cl.name}[/bold]")


@cover_letter_app.command("remove")
def remove_cover_letter(cover_letter_id: str = typer.Argument(...)):
    """Remove a cover letter if it is not associated with any jobs"""
    with get_db() as db:
        cl = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
        if not cl:
            console.print(f"Cover letter ID {cover_letter_id} not found")
            raise typer.Exit()
        if cl.jobs:
            console.print(f"Cannot remove cover letter [bold]{cl.name}[/bold] (used by {len(cl.jobs)} job(s))")
            raise typer.Exit()
        try:
            db.delete(cl)
            db.commit()
        except Exception:
            db.rollback()
            raise
        console.print(f"Removed cover letter [bold]{cl.name}[/bold]")
