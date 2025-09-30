from pydantic import BaseModel, Field
from db.models.teams_enums.enums import DirectionEnum

class TeamUpdate(BaseModel):
    name: str = Field(..., title="Название команды")
    description: str = Field(...,title="Описание команды")
    points: str = Field(...,title="Очки команды")
    task_completed: int = Field(...,title="Количество сделанных задач")

    region: str = Field(..., title="Регион")
    organization_id: int = Field(..., title="ID организации")
    leader_id: int = Field(..., title="ID лидера")