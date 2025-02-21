# app/core/config.py
import os
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My FastAPI Project"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"


settings = Settings()
