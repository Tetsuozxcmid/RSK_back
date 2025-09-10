from typing import Optional
from pydantic import BaseModel,Field,EmailStr
from pydantic.types import SecretStr
from sqlalchemy import Boolean
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class UserRegister(BaseModel):
    password: SecretStr = Field(..., min_length=8, example="password1232305")
    name: str = Field(..., example="userexample")
    email: EmailStr = Field(...,example="email@email.com")
    
    role: Optional[UserRole] = Field(
        default=UserRole.STUDENT, 
        example="student",
        description="Роль пользователя: student или teacher"
    )

class EmailSchema(BaseModel):
    email: EmailStr
    