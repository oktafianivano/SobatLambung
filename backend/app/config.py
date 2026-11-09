from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str 
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    DATABASE_URL: str
    FONNTE_TOKEN: str
    FONNTE_API_URL: str 

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()