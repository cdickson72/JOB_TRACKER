from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from .enums import JobStatus  # keep your current enum import


class JobCreate(BaseModel):
    company: str
    title: str
    location: Optional[str] = None
    salary_range: Optional[str] = None
    job_url: Optional[HttpUrl] = None
    source: Optional[str] = None
    resume_submitted: Optional[str] = None  # resume file name
    cover_letter_submitted: Optional[str] = None  # cover letter file name


class JobRead(BaseModel):
    id: str
    company: str
    title: str
    status: JobStatus
    applied_date: Optional[datetime]
    created_at: Optional[datetime]
    last_updated: Optional[datetime]

    class Config:
        orm_mode = True
