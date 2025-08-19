from pydantic import BaseModel
from pydantic import BaseModel
from typing import Optional

class TeamMemberResponse(BaseModel):
    user_id: int
    team_id: int
    is_leader: bool
    
    class Config:
        from_attributes = True



class TeamMemberResponse(BaseModel):
    user_id: int
    team_id: int
    is_leader: bool
    name: Optional[str] = ""
    surname: Optional[str] = ""
    patronymic: Optional[str] = ""
    region: Optional[str] = ""
    
    class Config:
        from_attributes = True