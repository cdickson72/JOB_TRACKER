import enum


class JobStatus(str, enum.Enum):
    APPLIED = "applied"
    RECRUITER = "recruiter"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
