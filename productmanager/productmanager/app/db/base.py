from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./test.db"

Base = declarative_base()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # ✅ 모든 모델 import 후 실행하도록 변경
# import app.models

# try:
#     Base.metadata.create_all(bind=engine)  # ✅ 모든 모델 import 후 실행
#     print("✅ 모든 테이블이 생성되었습니다.")
# except Exception as e:
#     print(f"🚨 테이블 생성 중 오류 발생: {e}")
