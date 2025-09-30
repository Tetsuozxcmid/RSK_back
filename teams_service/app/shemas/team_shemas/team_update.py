from pydantic import BaseModel, Field
from db.models.teams_enums.enums import DirectionEnum

class TeamUpdate(BaseModel):
    name: str = Field(..., title="Название команды")
    direction: DirectionEnum = Field(..., title="Направление команды")
    region: str = Field(..., title="Регион")
    organization_id: int = Field(..., title="ID организации")
    leader_id: int = Field(..., title="ID лидера")
