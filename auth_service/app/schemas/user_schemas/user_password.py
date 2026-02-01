from pydantic import BaseModel, SecretStr


class ChangePasswordSchema(BaseModel):
    current_password: SecretStr
    new_password: SecretStr
