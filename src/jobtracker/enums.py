import enum


class JobStatus(str, enum.Enum):
    APPLIED = "applied"
    RECRUITER = "recruiter"
    VIDEO_INTERVIEW = "video_interview"
    FIRST = "1st_interview"
    SECOND = "2nd_interview"
    FINAL = "final_interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
