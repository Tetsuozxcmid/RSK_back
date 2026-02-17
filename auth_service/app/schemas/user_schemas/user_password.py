from pydantic import BaseModel, SecretStr
from pydantic import BaseModel, EmailStr, Field

class ChangePasswordSchema(BaseModel):
    current_password: SecretStr
    new_password: SecretStr


class PasswordResetRequest(BaseModel):
    email_or_login: str = Field(..., description="Email или логин пользователя")