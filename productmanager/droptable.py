from sqlalchemy import create_engine, text

# ✅ 데이터베이스 파일 경로
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS sales_records"))
    conn.execute(text("""
        CREATE TABLE sales_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            client_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 0,
            sale_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    conn.commit()

print("✅ sales_records 테이블이 초기화되었습니다!")
