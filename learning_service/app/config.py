from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/learning_db"
    
    class Config:
        env_file = ".env"


settings = Settings()