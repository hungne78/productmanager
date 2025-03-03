# app/core/config.py
import os
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str   # ✅ 기본값 추가
    ALGORITHM: str
    PROJECT_NAME: str = "My FastAPI Project"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 

    class Config:
        env_file = ".env"


settings = Settings()
