from pydantic import BaseModel, ConfigDict
from typing import Optional

class CourseCreate(BaseModel):
    lesson_name: str
    lesson_number: int
    description: Optional[str] = None
    file_extension: str
    download_url: str

class CourseUpdate(BaseModel):
    lesson_name: Optional[str] = None
    lesson_number: Optional[int] = None
    description: Optional[str] = None
    file_extension: Optional[str] = None
    download_url: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    lesson_name: str
    lesson_number: int
    description: Optional[str]
    file_extension: str
    download_url: str
    is_completed: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
