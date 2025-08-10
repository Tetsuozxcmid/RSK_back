from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from db.models.teams_enums.enums import DirectionEnum

class TeamRegister(BaseModel):
    name: str = Field(..., title="Название команды")
    direction: DirectionEnum = Field(..., title="Направление команды")
    city: str = Field(..., title="Город")
    region: str = Field(..., title="Регион")
    organization_id: int = Field(..., title="ID организации")
    organization_name: str = Field(...,title="Организация")
    