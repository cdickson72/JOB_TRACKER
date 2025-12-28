import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm.exc import DetachedInstanceError

try:  # pragma: no cover - skip when project not on PYTHONPATH / not installed
    from jobtracker.models import Job, Resume
    from jobtracker.enums import JobStatus
except Exception:  # pragma: no cover - try to add repo root to PYTHONPATH, else skip
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    try:
        from jobtracker.models import Job, Resume  # noqa: F401
        from jobtracker.enums import JobStatus  # noqa: F401
    except Exception as exc2:
        pytest.skip(
            f"Missing runtime dependency or import error after adjusting PYTHONPATH: {exc2}",
            allow_module_level=True,
        )


def test_enum_can_read_lowercase_values(session):
    """Older DB rows used lowercase enum *values* (e.g., 'applied'). Ensure we can read them."""

    # Insert a raw row with lowercase status string to simulate pre-fix data
    record = {
        "id": str(uuid.uuid4()),
        "company": "Acme",
        "title": "Engineer",
        "status": "applied",
        "created_at": datetime.now(timezone.utc),
    }

    session.execute(Job.__table__.insert().values(**record))
    session.commit()

    job = session.query(Job).first()

    # The ORM should map the stored lowercase value to the enum (and .value should equal the stored string)
    assert job is not None
    assert isinstance(job.status, JobStatus)
    assert job.status.value == "applied"


def test_list_jobs_eager_loads_and_prints_once(monkeypatch, session, capsys):
    """Ensure that the CLI list flow eager-loads relationships (no DetachedInstanceError)
    and that the printed table appears only once (fix for duplicate prints)."""

    # Create a resume and job that references it
    resume = Resume(name="Test Resume", file_path="/tmp/res.pdf")
    session.add(resume)
    session.commit()

    job = Job(
        id=str(uuid.uuid4()),
        company="Example",
        title="Dev",
        resume_id=resume.id,
        created_at=datetime.now(timezone.utc),
    )
    session.add(job)
    session.commit()

    # Reproduce the *old* faulty behavior: query WITHOUT eager loading then close session
    with monkeypatch.context():
        import jobtracker.db as dbmod

        # use the patched SessionLocal already provided by the session fixture
        with dbmod.get_db() as db:
            queried = db.query(Job).order_by(Job.created_at.desc()).all()

        # After the contextmanager closes the session, lazy-loading resume should raise
        with pytest.raises(DetachedInstanceError):
            # Accessing the lazy relationship should fail
            _ = queried[0].resume.name

    # Verify eager loading works via an explicit query using the same options the CLI uses
    from sqlalchemy.orm import joinedload
    import jobtracker.db as dbmod

    with dbmod.get_db() as db:
        eager_jobs = db.query(Job).options(joinedload(Job.resume), joinedload(Job.cover_letter)).all()
        assert eager_jobs[0].resume.name == "Test Resume"

    # And verify the CLI `list` command prints only one table header
    from jobtracker.cli import cli_jobs

    cli_jobs.list_jobs()
    out = capsys.readouterr().out
    assert out.count("Tracked Job Applications") == 1
