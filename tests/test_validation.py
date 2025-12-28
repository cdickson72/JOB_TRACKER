import pytest
from pydantic import ValidationError
from jobtracker.schemas import JobCreate, ResumeCreate, CoverLetterCreate, JobUpdate


def test_salary_normalization():
    inp = "120000 - 190000"
    job = JobCreate(company="Co", title="T", salary_range=inp)
    assert job.salary_range == "$120,000 - $190,000"


def test_salary_invalid_raises():
    with pytest.raises(ValidationError):
        JobCreate(company="Co", title="T", salary_range="not a salary")


def test_resume_file_path_validation(tmp_path):
    # valid file
    p = tmp_path / "resume.txt"
    p.write_text("ok")
    r = ResumeCreate(name="Me", file_path=str(p))
    assert r.file_path == str(p)

    # invalid file
    with pytest.raises(ValidationError):
        ResumeCreate(name="Me", file_path=str(p.parent / "missing.txt"))


def test_cover_letter_file_path_validation(tmp_path):
    p = tmp_path / "cover.txt"
    p.write_text("ok")
    cl = CoverLetterCreate(name="MeCL", file_path=str(p))
    assert cl.file_path == str(p)

    with pytest.raises(ValidationError):
        CoverLetterCreate(name="MeCL", file_path=str(p.parent / "missing.txt"))


def test_jobupdate_salary_normalization():
    ju = JobUpdate(salary_range="120000 - 190000")
    assert ju.salary_range == "$120,000 - $190,000"
