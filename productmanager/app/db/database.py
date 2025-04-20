from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = settings.DATABASE_URL  # ✅ 설정값을 직접 사용

connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)  # ✅ 마리아DB

# engine = create_engine(
#     settings.DATABASE_URL,
#     connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
#     echo=False
# )  #sqlite

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
