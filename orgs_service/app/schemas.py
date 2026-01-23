from pydantic import BaseModel
from typing import Optional
from db.models.orgs import Orgs

class OrgCreateSchema(BaseModel):
    inn: Optional[str] = None
    



