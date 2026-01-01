from pydantic import BaseModel, HttpUrl, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from .enums import JobStatus  # keep your current enum import
from pathlib import Path
import re


class JobCreate(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[HttpUrl] = None
    source: Optional[str] = None
    resume_submitted: Optional[str] = None  # resume file name
    cover_letter_submitted: Optional[str] = None  # cover letter file name

    model_config = ConfigDict(from_attributes=True)

    @field_validator("company", "title")
    def not_empty(cls, v: str) -> str:  # type: ignore[override]
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("salary_range")
    def salary_format(cls, v: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if v is None:
            return v
        s = v.strip()
        # Allow explicit 'none listed'
        if s.lower() == "none listed":
            return s
        # Accept patterns like "$120,000 - $190,000" or "120000 - 190000" and normalize
        m = re.match(r"^\$?([\d,]+)\s*-\s*\$?([\d,]+)$", s)
        if not m:
            raise ValueError("salary_range must be in format '$120,000 - $190,000' or 'none listed'")
        low, high = m.group(1), m.group(2)

        # Normalize to include dollar sign and commas
        def norm(x: str) -> str:
            x = x.replace(",", "")
            return f"${int(x):,}"

        return f"{norm(low)} - {norm(high)}"


class JobUpdate(BaseModel):
    # Provide explicit defaults so fields are truly optional for partial updates
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[HttpUrl] = None
    source: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("company", "title")
    def not_empty(cls, v: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if v is None:
            return v
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("salary_range")
    def salary_format(cls, v: Optional[str]) -> Optional[str]:  # type: ignore[override]
        if v is None:
            return v
        # reuse same validation as JobCreate
        return JobCreate.salary_format.__func__(None, v)


class JobRead(BaseModel):
    id: str
    company: str
    title: str
    status: JobStatus
    applied_date: Optional[datetime]
    created_at: Optional[datetime]
    last_updated: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ResumeCreate(BaseModel):
    name: str
    file_path: str
    tags: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("name")
    def not_empty(cls, v: str) -> str:  # type: ignore[override]
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("file_path")
    def path_must_exist(cls, v: str) -> str:  # type: ignore[override]
        p = Path(v).expanduser()
        if not p.exists() or not p.is_file():
            raise ValueError(f"file_path does not exist or is not a file: {v}")
        return str(p)


class CoverLetterCreate(BaseModel):
    name: str
    file_path: str
    tags: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("name")
    def not_empty(cls, v: str) -> str:  # type: ignore[override]
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()

    @field_validator("file_path")
    def path_must_exist(cls, v: str) -> str:  # type: ignore[override]
        p = Path(v).expanduser()
        if not p.exists() or not p.is_file():
            raise ValueError(f"file_path does not exist or is not a file: {v}")
        return str(p)
