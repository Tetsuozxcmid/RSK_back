from pydantic import BaseModel, ConfigDict
from typing import Optional
from db.models.user_enum import UserEnum


class UserRoleUpdate(BaseModel):
    role: UserEnum
    
    class Config:
        pass

class OrganizationSimple(BaseModel):
    id: int
    name: str
    full_name: Optional[str] = None
    short_name: Optional[str] = None
    inn: Optional[int] = None
    region: Optional[str] = None
    type: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
class ProfileResponse(BaseModel):
    NameIRL: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    Surname: Optional[str] = None
    Patronymic: Optional[str] = None
    Description: Optional[str] = None
    Region: Optional[str] = None
    Type: Optional[UserEnum] = None
    Organization: Optional[OrganizationSimple] = None
    Organization_id: Optional[int] = None
    team: Optional[str] = None
    team_id: Optional[int] = None

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


class ProfileUpdate(BaseModel):
    NameIRL: Optional[str] = None
    email: Optional[str] = None
    Surname: Optional[str] = None
    Patronymic: Optional[str] = None
    Description: Optional[str] = None
    Region: Optional[str] = None
    Type: Optional[UserEnum] = None
    Organization_id: Optional[int] = None


class ProfileJoinedTeamUpdate(BaseModel):
    user_id: int
    team: Optional[str] = None
    team_id: Optional[int] = None


class ProfileJoinedOrg(BaseModel):
    user_id: int
    Organization: Optional[str] = None
    Organization_id: Optional[int] = None
