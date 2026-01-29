from pydantic import BaseModel

class OrgCreateSchema(BaseModel):
    inn: str = None
    type: str = None
    

class OrgResponse(BaseModel):
    id: int
    full_name: str
    short_name: str
    inn: int
    region: str
    type: str
    star: float
    knowledge_skills_z: float
    knowledge_skills_v: float
    digital_env_e: float
    data_protection_z: float
    data_analytics_d: float
    automation_a: float
    members_count: int
    teams_count: int
