from pydantic import BaseModel,Field,EmailStr
from pydantic.types import SecretStr

class UserRegister(BaseModel):
    password: SecretStr = Field(..., min_length=8, example="password1232305")
    name: str = Field(..., example="userexample")
    email: EmailStr = Field(...,example="email@email.com")