from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from db.models.teams_enums.enums import DirectionEnum

class TeamRegister(BaseModel):
    name: str = Field(..., title="Название команды")
    description: str = Field(...,title="Описание команды")
    points: str = Field(...,title="Очки команды")
    task_completed: int = Field(...,title="Количество сделанных задач")
    region: str = Field(..., title="Регион")
    organization_name: str = Field(...,title="Организация")
    