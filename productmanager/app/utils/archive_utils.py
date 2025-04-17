from sqlalchemy import text
from sqlalchemy.orm import Session

def create_archive_table_if_not_exists(year: int, db: Session):
    archive_table = f"sales_records_{year}"
    sql = f"""
    CREATE TABLE IF NOT EXISTS {archive_table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        client_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 0,
        return_amount FLOAT NOT NULL DEFAULT 0.0,
        subsidy_amount FLOAT NOT NULL DEFAULT 0.0,
        total_amount FLOAT NOT NULL DEFAULT 0.0,
        sale_datetime DATETIME NOT NULL
    );
    """
    db.execute(text(sql))
    db.commit()
    print(f"✅ 테이블 생성 완료: {archive_table}")



def archive_sales_for_year_if_not_archived(year: int, db: Session):
    archive_table = f"sales_records_{year}"
    print(f"📦 아카이브 테이블 체크: {archive_table}")

    # ✅ SQLite 호환 테이블 존재 여부 확인
    check_sql = text("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name = :table_name
    """)
    result = db.execute(check_sql, {"table_name": archive_table}).first()

    if result:
        print(f"✅ 이미 존재하는 아카이브 테이블: {archive_table}")
        return

    print(f"📂 아카이브 테이블 생성 시작: {archive_table}")
    create_archive_table_if_not_exists(year, db)

