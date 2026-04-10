from pydantic import BaseModel, ConfigDict,Field
from typing import List, Optional
from db.models.user_enum import UserEnum,UserEnumForAdmin,UserEnumForUser


class UserRoleUpdate(BaseModel):
    role: UserEnum

    class Config:
        pass

class UserRoleAdmin(BaseModel):
    role: UserEnum
    user_id: int

    class Config:
        pass

class UserRoleUpdateForUser(BaseModel):
    role: UserEnumForUser  

class UserRoleAdmin(BaseModel):
    role: UserEnumForAdmin  
    user_id: int

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
    is_learned: bool

    class Config:
        from_attributes = True


class UpdateLearningStatusRequest(BaseModel):
    user_id: int
    is_learned: bool


class BulkUpdateLearningRequest(BaseModel):
    users: List[dict]


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
    Organization_id: Optional[int] = Field(None, alias="organization_id")


class OAuthProfileSyncRequest(BaseModel):
    user_id: int
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    auth_provider: Optional[str] = None


class ProfileJoinedTeamUpdate(BaseModel):
    user_id: int
    team: Optional[str] = None
    team_id: Optional[int] = None


class ProfileJoinedOrg(BaseModel):
    user_id: int
    Organization: Optional[str] = None
    Organization_id: Optional[int] = None
