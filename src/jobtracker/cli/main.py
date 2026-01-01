import typer
from jobtracker.cli.cli_jobs import job_app
from jobtracker.cli.cli_resume import resume_app
from jobtracker.cli.cli_cover_letter import cover_letter_app
from jobtracker.db import init_db
from jobtracker.cli.cli_notes import note_app


app = typer.Typer(help="JobTracker - CLI job application tracker")

# Add sub-apps
app.add_typer(job_app, name="job")
app.add_typer(resume_app, name="resume")
app.add_typer(cover_letter_app, name="cover-letter")
app.add_typer(note_app, name="note")


@app.callback()
def main():
    """Initialize database (if needed)"""
    init_db()


if __name__ == "__main__":
    app()
