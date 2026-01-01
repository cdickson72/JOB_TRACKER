import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SqlEnum
from sqlalchemy.orm import relationship
from .db import Base
from .enums import JobStatus


def generate_uuid():
    return str(uuid.uuid4())


def _now_utc():
    return datetime.now(timezone.utc)


# -----------------------------
# Resume Model
# -----------------------------
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    tags = Column(String)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    # Back-reference to jobs that used this resume
    jobs = relationship("Job", back_populates="resume")


# -----------------------------
# Cover Letter Model
# -----------------------------
class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    tags = Column(String)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    # Back-reference to jobs that used this cover letter
    jobs = relationship("Job", back_populates="cover_letter")


# -----------------------------
# Job Model
# -----------------------------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    company = Column(String, nullable=False)
    title = Column(String, nullable=False)
    location = Column(String)
    salary_range = Column(String)
    job_url = Column(String)
    source = Column(String)
    # Use the enum's values (e.g., 'applied') when storing in the DB so
    # existing rows with lowercase values remain readable.
    status = Column(
        SqlEnum(
            JobStatus,
            native_enum=False,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=JobStatus.APPLIED,
    )

    applied_date = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    # Foreign Keys
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=True)
    cover_letter_id = Column(String, ForeignKey("cover_letters.id"), nullable=True)

    ai_summary = Column(Text)

    # Relationships
    resume = relationship("Resume", back_populates="jobs")
    cover_letter = relationship("CoverLetter", back_populates="jobs")
    notes = relationship("Note", back_populates="job", cascade="all, delete-orphan")


# -----------------------------
# Note Model
# -----------------------------
class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    job = relationship("Job", back_populates="notes")
