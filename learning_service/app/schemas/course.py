from pydantic import BaseModel, ConfigDict

class CourseResponse(BaseModel):
    id: int
    lesson_name: str
    lesson_number: int
    description: str
    file_extension: str
    download_url: str

    model_config = ConfigDict(from_attributes=True)