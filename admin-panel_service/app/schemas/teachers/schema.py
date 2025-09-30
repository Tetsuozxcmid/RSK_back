from pydantic import BaseModel
from typing import List

class Teacher(BaseModel):
    id: int
    first_name: str
    second_name: str
    last_name: str

    documents_file: str
    is_approved: bool = False

class TeachersList(BaseModel):
    teachers: List[Teacher]