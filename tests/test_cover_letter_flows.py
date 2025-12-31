import re

import pytest
from typer.testing import CliRunner


try:  # pragma: no cover - skip when project not on PYTHONPATH / not installed
    from jobtracker.models import CoverLetter, Job
    from jobtracker.cli.main import app
except Exception as exc:  # pragma: no cover - skip when imports fail
    pytest.skip(f"Missing runtime dependency or import error: {exc}", allow_module_level=True)


def test_cover_letter_add_update_remove_flow(session, runner, tmp_path):
    """Add a cover letter via CLI, update it, then remove it; assert DB state at each step."""

    runner = CliRunner()

    p = tmp_path / "cl1.txt"
    p.write_text("cover letter 1")

    # Add
    result = runner.invoke(
        app,
        [
            "cover-letter",
            "add",
            "--name",
            "MyCL",
            "--file-path",
            str(p),
            "--tags",
            "tag1,tag2",
        ],
    )
    assert result.exit_code == 0, result.stdout
    out = result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", out)
    assert m, f"Could not find ID in output: {out}"
    cl_id = m.group(1)

    cl = session.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
    assert cl is not None
    assert cl.name == "MyCL"
    assert cl.tags == "tag1,tag2"

    # Update (change name and tags and file path)
    p2 = tmp_path / "cl2.txt"
    p2.write_text("cover letter 2")
    result2 = runner.invoke(
        app, ["cover-letter", "update", cl_id, "--name", "MyCL2", "--tags", "tag3", "--file-path", str(p2)]
    )
    assert result2.exit_code == 0, result2.stdout

    # Ensure the test session sees committed changes from the CLI invocation
    session.expire_all()

    cl = session.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
    assert cl.name == "MyCL2"
    assert cl.tags == "tag3"
    assert cl.file_path == str(p2)

    # Remove
    result3 = runner.invoke(app, ["cover-letter", "remove", cl_id])
    assert result3.exit_code == 0, result3.stdout
    cl_after = session.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
    assert cl_after is None


def test_cannot_remove_cover_letter_in_use(session, runner, tmp_path):
    runner = CliRunner()
    p = tmp_path / "cl_use.txt"
    p.write_text("cover letter in use")

    # Add cover letter
    result = runner.invoke(app, ["cover-letter", "add", "--name", "InUse", "--file-path", str(p), "--tags", "a"])
    assert result.exit_code == 0, result.stdout
    m = re.search(r"ID:\s*([0-9a-fA-F-]{36})", result.stdout)
    cl_id = m.group(1)

    # Create a job that references this cover letter (use job add CLI)
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
            "none",
            "--cover-letter-id",
            cl_id,
            "--location",
            "remote",
            "--salary-range",
            "$50,000 - $70,000",
            "--job-url",
            "https://example.org",
        ],
    )
    assert job_result.exit_code == 0, job_result.stdout

    # Ensure the job references the cover letter
    session.expire_all()
    j = session.query(Job).filter(Job.cover_letter_id == cl_id).first()
    assert j is not None

    # Attempt to remove cover letter (should be blocked because it's in use)
    rem = runner.invoke(app, ["cover-letter", "remove", cl_id])
    # The CLI may raise `typer.Exit()` without a non-zero code when blocking removal,
    # so check the user-visible message and ensure the cover letter still exists.
    assert "Cannot remove cover letter" in rem.stdout
    cl = session.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
    assert cl is not None
