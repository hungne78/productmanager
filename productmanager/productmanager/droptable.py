import sqlite3

# SQLite 데이터베이스 파일 경로 (FastAPI 프로젝트에서 사용 중인 DB 파일)
db_path = "test.db"  # ❗ 실제 사용하는 DB 파일명을 확인하세요

# SQLite 연결
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 테이블 변경 SQL 실행
try:
    cursor.executescript("""
    ALTER TABLE sales_records RENAME TO sales_records_old;

    CREATE TABLE sales_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        client_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        sale_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    INSERT INTO sales_records (id, employee_id, client_id, product_id, quantity, created_at, updated_at)
    SELECT id, employee_id, client_id, product_id, quantity, created_at, updated_at FROM sales_records_old;

    DROP TABLE sales_records_old;
    """)
    conn.commit()
    print("✅ 테이블 변경 완료!")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
finally:
    conn.close()
