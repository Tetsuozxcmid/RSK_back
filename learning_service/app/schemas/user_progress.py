from pydantic import BaseModel


class UserProgressUpdate(BaseModel):
    is_completed: bool


class UserProgressResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    is_completed: bool

    model_config = {"from_attributes": True}