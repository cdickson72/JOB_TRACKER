import re

import pytest
from typer.testing import CliRunner


try:  # pragma: no cover - skip when project not on PYTHONPATH / not installed
    from jobtracker.models import Resume, Job
    from jobtracker.cli.main import app
except Exception as exc:  # pragma: no cover - skip when imports fail
    pytest.skip(f"Missing runtime dependency or import error: {exc}", allow_module_level=True)


def test_resume_add_update_remove_flow(session, runner, tmp_path):
    runner = CliRunner()
    p = tmp_path / "r1.txt"
    p.write_text("resume 1")

    # Add
    result = runner.invoke(app, ["resume", "add", "--name", "MyRes", "--file-path", str(p), "--tags", "x"])
    assert result.exit_code == 0, result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", result.stdout)
    assert m, f"Could not find ID in output: {result.stdout}"
    r_id = m.group(1)

    r = session.query(Resume).filter(Resume.id == r_id).first()
    assert r is not None
    assert r.name == "MyRes"

    # Update
    p2 = tmp_path / "r2.txt"
    p2.write_text("resume 2")
    result2 = runner.invoke(app, ["resume", "update", r_id, "--name", "MyRes2", "--tags", "y", "--file-path", str(p2)])
    assert result2.exit_code == 0, result2.stdout
    session.expire_all()
    r = session.query(Resume).filter(Resume.id == r_id).first()
    assert r.name == "MyRes2"
    assert r.file_path == str(p2)

    # Remove
    result3 = runner.invoke(app, ["resume", "remove", r_id])
    assert result3.exit_code == 0, result3.stdout
    r_after = session.query(Resume).filter(Resume.id == r_id).first()
    assert r_after is None


def test_cannot_remove_resume_in_use(session, runner, tmp_path):
    runner = CliRunner()
    p = tmp_path / "r_use.txt"
    p.write_text("resume in use")

    # Add resume
    result = runner.invoke(app, ["resume", "add", "--name", "InUseR", "--file-path", str(p), "--tags", "a"])
    assert result.exit_code == 0, result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", result.stdout)
    r_id = m.group(1)

    # Create job referencing this resume
    job_result = runner.invoke(
        app,
        [
            "job",
            "add",
            "--company",
            "UsingCo",
            "--title",
            "Dev",
            "--source",
            "Manual",
            "--applied-date",
            "2025-01-01",
            "--resume-id",
            r_id,
            "--cover-letter-id",
            "none",
            "--location",
            "remote",
            "--salary-range",
            "$50,000 - $70,000",
            "--job-url",
            "https://example.org",
        ],
    )
    assert job_result.exit_code == 0, job_result.stdout

    session.expire_all()
    j = session.query(Job).filter(Job.resume_id == r_id).first()
    assert j is not None

    rem = runner.invoke(app, ["resume", "remove", r_id])
    # Check message and that resume still exists
    assert "Cannot remove resume" in rem.stdout
    r = session.query(Resume).filter(Resume.id == r_id).first()
    assert r is not None
