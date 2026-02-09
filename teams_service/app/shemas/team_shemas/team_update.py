from pydantic import BaseModel, Field
from typing import Optional
from db.models.teams_enums.enums import DirectionEnum


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, title="Название команды")
    direction: Optional[DirectionEnum] = Field(None, title="Направление команды")
    region: Optional[str] = Field(None, title="Регион")
    organization_id: Optional[int] = Field(None, title="ID организации")  
    points: Optional[int] = Field(None, title="Очки")
    description: Optional[str] = Field(None, title="Описание команды")
    tasks_completed: Optional[int] = Field(None, title="Количество выполненных задач")