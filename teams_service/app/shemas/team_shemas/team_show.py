from pydantic import BaseModel, Field
from typing import Optional
from db.models.teams_enums.enums import DirectionEnum


class TeamShow(BaseModel):
    name: str = Field(..., title="Название команды")
    direction: DirectionEnum = Field(..., title="Направление команды")
    region: str = Field(..., title="Регион")
    organization_id: str = Field(..., title="id организации")
    organization_name: str = Field(..., title="Название организации")
    points: int = Field(0, title="Очки")
    description: Optional[str] = Field(None, title="Описание команды")
    tasks_completed: int = Field(0, title="Количество выполненных задач")
