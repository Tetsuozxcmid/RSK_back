from enum import Enum
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timedelta


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
    "Автоматизация": CategoryEnum.AUTOMATION,
}


class TaskReviewRequest(BaseModel):
    status: TaskStatus
    description: Optional[str] = None


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

    class Config:
        from_attributes = True


class ProjectCreate(ProjectBase):
    pass


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    prize_points: int = 0
    materials: Optional[List[dict]] = []

    class Config:
        from_attributes = True


class TaskRead(TaskBase):
    id: int
    project_id: int
    status: TaskStatus
    team_id: Optional[int] = None
    leader_id: Optional[int] = None
    created_at: datetime


class ProjectRead(ProjectBase):
    id: int
    tasks: List[TaskRead] = []


class TaskOut(TaskBase):
    id: int
    project_id: int
    status: TaskStatus


class TaskSubmissionRead(BaseModel):
    id: int
    task_id: int
    team_id: int
    text_description: Optional[str] = None
    result_url: Optional[str] = None

    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    status: TaskStatus
    moderator_id: Optional[int] = None

    time: Optional[int] = None  

    @field_validator("time", mode="before")
    @classmethod
    def calc_time(cls, v, info):
        submitted_at = info.data.get("submitted_at")
        if not submitted_at:
            return None

        expires_at = submitted_at + timedelta(minutes=10)
        remaining = int((expires_at - datetime.utcnow()).total_seconds())
        return max(remaining, 0)

    class Config:
        from_attributes = True


class TaskSubmitRequest(BaseModel):
    text_description: Optional[str] = None
    result_url: Optional[str] = None


class TaskCreate(TaskBase):
    pass



ProjectRead.model_rebuild()
TaskRead.model_rebuild()
