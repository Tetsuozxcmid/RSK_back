from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: int
    DB_NAME: str
    
    RSK_BOT_URL: str
    RSK_ORGS_URL: str
    USER_PROFILE_URL: str

    SECRET_KEY: str
    ALGORITHM: str
    

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        
    model_config = SettingsConfigDict(env_file='.env',env_file_encoding='utf-8')


settings = Settings()

def get_auth_data():
    return {"secret_key" : settings.SECRET_KEY,"algorithm" : settings.ALGORITHM}






    

