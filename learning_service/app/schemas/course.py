from pydantic import BaseModel, ConfigDict

class CourseResponse(BaseModel):
    id: int
    lesson_name: str
    lesson_number: int
    file_extension: str
    download_url: str
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


class CourseUpdate(BaseModel):
    is_completed: bool