from pydantic import BaseModel

class OrgCreateSchema(BaseModel):
    inn: str = None
    type: str = None
    

