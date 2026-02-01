from typing import Optional
from pydantic import BaseModel
from db.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    course_id: int
    file_url: str


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    file_url: str
    status: SubmissionStatus
    expires_at: Optional[float] = None

    model_config = {"from_attributes": True}


class SubmissionReview(BaseModel):
    status: SubmissionStatus
    description: str
