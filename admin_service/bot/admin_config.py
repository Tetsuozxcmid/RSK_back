from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    ADMIN_IDS: str
    ADMIN_SECRET_KEY: str

    @property
    def admin_ids(self) -> List[int]:

        return [int(id_.strip()) for id_ in self.ADMIN_IDS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
