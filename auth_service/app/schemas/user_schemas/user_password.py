from pydantic import AliasChoices, BaseModel, Field, SecretStr


class ChangePasswordSchema(BaseModel):
    current_password: SecretStr
    new_password: SecretStr


class PasswordResetRequest(BaseModel):
    email_or_login: str = Field(
        ...,
        validation_alias=AliasChoices("email_or_login", "email", "login"),
        description="Email or login for password reset",
    )
