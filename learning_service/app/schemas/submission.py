from pydantic import BaseModel
from app.db.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    user_id: int
    course_id: int
    file_url: str


class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    file_url: str
    status: SubmissionStatus

    model_config = {"from_attributes": True}


class SubmissionReview(BaseModel):
    status: SubmissionStatus