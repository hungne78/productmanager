from sqlalchemy import create_engine, text

DATABASE_URL = "sqlite:///./test.db"  # SQLite 파일 경로 수정
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with engine.connect() as connection:
    connection.execute(text("ALTER TABLE products ADD COLUMN incentive FLOAT DEFAULT 0;"))

print("✅ `incentive` 컬럼 추가 완료!")
