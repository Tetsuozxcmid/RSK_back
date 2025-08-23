from pydantic import BaseModel,Field


class UserGet(BaseModel):
    
    name: str = Field(..., example="userexample")


class UserOut(BaseModel):
    id: int
    name: str
    email: str | None
    
    class Config:
        from_attributes = True 