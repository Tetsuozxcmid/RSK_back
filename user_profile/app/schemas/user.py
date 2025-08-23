from pydantic import BaseModel
from typing import Optional
from db.models.user_enum import UserEnum


class ProfileResponse(BaseModel):
    NameIRL: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    Surname: Optional[str] = None
    Patronymic: Optional[str] = None
    Description: Optional[str] = None
    Region: Optional[str] = None
    Type: Optional[UserEnum] = None
    Organization: Optional[str] = None
    team: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileCreateSchema(BaseModel):
    NameIRL: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    Surname: Optional[str] = None
    Patronymic: Optional[str] = None
    Description: Optional[str] = None
    Region: Optional[str] = None
    Type: Optional[UserEnum] = None
    Organization: Optional[str] = None
    Organization_id: Optional[int] = None
    team_id: Optional[int] = None
    team: Optional[str] = None


class ProfileUpdate(BaseModel):
    id: Optional[int]
    NameIRL: Optional[str] = None
    email: Optional[str] = None
    Surname: Optional[str] = None
    Patronymic: Optional[str] = None
    Description: Optional[str] = None
    Region: Optional[str] = None
    Type: Optional[UserEnum] = None
    Organization: Optional[str] = None
    team: Optional[str] = None
