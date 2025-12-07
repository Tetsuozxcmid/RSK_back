from pydantic import BaseModel, Field
from typing import Optional

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, title="Название команды")
    description: Optional[str] = Field(None, title="Описание команды")