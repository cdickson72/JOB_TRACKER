import re

import pytest
from typer.testing import CliRunner


try:  # pragma: no cover - skip when project not on PYTHONPATH / not installed
    from jobtracker.models import Job
    from jobtracker import db as dbmod
    from jobtracker.cli.main import app
except Exception as exc:  # pragma: no cover - skip when imports fail
    pytest.skip(f"Missing runtime dependency or import error: {exc}", allow_module_level=True)


def test_transaction_rollback_on_commit_failure(monkeypatch, session):
    """Simulate a commit failure during `job add` and assert the DB state is rolled back."""

    # Arrange: replace SessionLocal with one that returns sessions whose commit raises
    def broken_session_factory(*args, **kwargs):
        s = dbmod.SessionLocal(*args, **kwargs)

        def bad_commit():
            raise RuntimeError("simulated commit failure")

        s.commit = bad_commit
        return s

    monkeypatch.setattr(dbmod, "SessionLocal", broken_session_factory)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "job",
            "add",
            "--company",
            "BrokenCo",
            "--title",
            "Engineer",
            "--source",
            "Manual",
            "--applied-date",
            "2025-01-01",
            "--resume-id",
            "none",
            "--cover-letter-id",
            "none",
            "--location",
            "remote",
            "--salary-range",
            "$60,000 - $80,000",
            "--job-url",
            "https://example.com",
        ],
    )

    # The CLI should return a non-zero exit code due to the simulated commit error
    assert result.exit_code != 0

    # Ensure nothing was committed to the DB
    remaining = session.query(Job).filter(Job.company == "BrokenCo").all()
    assert remaining == []


def test_cli_add_status_remove_flow(session, runner):
    """Add a job via the CLI, change its status, then remove it; assert DB state at each step."""

    runner = CliRunner()

    # Add
    result = runner.invoke(
        app,
        [
            "job",
            "add",
            "--company",
            "FlowCo",
            "--title",
            "Engineer",
            "--source",
            "Manual",
            "--applied-date",
            "2025-01-01",
            "--resume-id",
            "none",
            "--cover-letter-id",
            "none",
            "--location",
            "remote",
            "--salary-range",
            "$60,000 - $80,000",
            "--job-url",
            "https://example.com",
        ],
    )

    assert result.exit_code == 0
    out = result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", out)
    assert m, f"Could not find ID in output: {out}"
    job_id = m.group(1)

    # Status change
    result2 = runner.invoke(app, ["job", "status", job_id, "interview"])
    assert result2.exit_code == 0

    job = session.query(Job).filter(Job.id == job_id).first()
    assert job is not None
    assert job.status.value == "interview"

    # Remove
    result3 = runner.invoke(app, ["job", "remove", job_id])
    assert result3.exit_code == 0
    job_after = session.query(Job).filter(Job.id == job_id).first()
    assert job_after is None


def test_job_url_saved_as_string(session, runner):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "job",
            "add",
            "--company",
            "URLCo",
            "--title",
            "Engineer",
            "--source",
            "Manual",
            "--applied-date",
            "2025-01-01",
            "--resume-id",
            "none",
            "--cover-letter-id",
            "none",
            "--location",
            "remote",
            "--salary-range",
            "$60,000 - $80,000",
            "--job-url",
            "https://example.com",
        ],
    )

    assert result.exit_code == 0, result.stdout
    # find the created job and assert job_url is stored as a string
    out = result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", out)
    assert m, f"Could not find ID in output: {out}"
    job_id = m.group(1)

    job = session.query(Job).filter(Job.id == job_id).first()
    assert job is not None
    assert isinstance(job.job_url, str)
    # HttpUrl may normalize to include a trailing slash; accept either form
    assert job.job_url.rstrip("/") == "https://example.com"
