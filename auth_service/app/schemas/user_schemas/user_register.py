from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from pydantic.types import SecretStr
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    MODER = "moder"


class UserRegister(BaseModel):
    password: SecretStr = Field(..., min_length=8, example="password1232305")
    email: EmailStr = Field(..., example="email@email.com")
    name: Optional[str] = Field(None, example="Иван Иванов")

    role: Optional[UserRole] = Field(
        default=UserRole.STUDENT,
        example="student",
        description="Роль пользователя: student или teacher или moder",
    )


class EmailSchema(BaseModel):
    email: EmailStr
