from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CategoryEnum(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    INTERACTION = "INTERACTION"
    ENVIRONMENT = "ENVIRONMENT"
    PROTECTION = "PROTECTION"
    DATA = "DATA"
    AUTOMATION = "AUTOMATION"


CATEGORY_MAP = {
    "Знания": CategoryEnum.KNOWLEDGE,
    "Взаимодействие": CategoryEnum.INTERACTION,
    "Среда": CategoryEnum.ENVIRONMENT,
    "Защита": CategoryEnum.PROTECTION,
    "Данные": CategoryEnum.DATA,
    "Автоматизация": CategoryEnum.AUTOMATION
}


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    organization_name: Optional[str] = None
    star_index: int = 0
    star_category: CategoryEnum
    level_number: int = 1

    
    @field_validator("star_category", mode="before")
    @classmethod
    def map_russian_category(cls, v):
        if isinstance(v, str) and v in CATEGORY_MAP:
            return CATEGORY_MAP[v]
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int
    tasks: List["TaskRead"] = []

    class Config:
        orm_mode = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    prize_points: int = 0
    materials: Optional[List[dict]] = []


class TaskCreate(TaskBase):
    project_id: int


class TaskRead(TaskBase):
    id: int
    project_id: int
    status: TaskStatus
    team_id: Optional[int]
    leader_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True


class TaskSubmissionBase(BaseModel):
    text_description: Optional[str] = None
    result_url: Optional[str] = None


class TaskSubmissionCreate(TaskSubmissionBase):
    task_id: int
    team_id: int


class TaskSubmissionRead(TaskSubmissionBase):
    id: int
    task_id: int
    team_id: int
    submitted_at: datetime
    status: TaskStatus
    moderator_id: Optional[int]
    reviewed_at: Optional[datetime]

    class Config:
        orm_mode = True


class TaskStartRequest(BaseModel):
    team_id: int
    leader_id: int



ProjectRead.update_forward_refs()
TaskRead.update_forward_refs()

