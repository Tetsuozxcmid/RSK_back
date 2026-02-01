from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    WORKSHOP_SERVICE_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def RABBIT_URL(self):
        return self.RABBIT_URL

    @property
    def WORKSHOP_URL(self):
        return self.WORKSHOP_SERVICE_URL


settings = Settings()
