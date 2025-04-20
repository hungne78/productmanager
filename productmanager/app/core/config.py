# app/core/config.py
import os
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    DATABASE_URL: str
    SQLALCHEMY_DATABASE_URI: str = Field(..., alias="DATABASE_URL")  # ← 이 줄 추가
    PROJECT_NAME: str = "My FastAPI Project"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
