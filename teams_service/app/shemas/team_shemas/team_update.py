from pydantic import BaseModel, Field
from db.models.teams_enums.enums import DirectionEnum
from typing import Optional


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, title="Название команды")
    direction: Optional[DirectionEnum] = Field(None, title="Направление команды")
    region: Optional[str] = Field(None, title="Регион")
    description: Optional[str] = Field(None, title="Описание команды")
    points: Optional[int] = Field(None, title="Очки")
    tasks_completed: Optional[int] = Field(None, title="Количество выполненных задач")
