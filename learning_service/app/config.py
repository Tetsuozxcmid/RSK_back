from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: int
    DB_NAME: str

    ALGORITHM: str
    SECRET_KEY: str

    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_PORT: int
    SMTP_SERVER: str
    SENDER_EMAIL: str

    AUTH_SERVICE_URL: str

    REDIS_URL: str = "redis://redis:6379"

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
