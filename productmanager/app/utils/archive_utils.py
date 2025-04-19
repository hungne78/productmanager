from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

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

def migrate_last_year_sales(db: Session):
    """
    ⏰ 매년 1 월 1 일 03:00 에 호출:
    ① sales_records_{last_year} 테이블이 없으면 만들고
    ② 직전 연도 데이터 INSERT … SELECT
    ③ 원본(sales_records)에서 직전 연도 데이터 DELETE
    """
    last_year = datetime.now().year - 1
    archive_table = f"sales_records_{last_year}"

    # 1) 테이블 보장
    create_archive_table_if_not_exists(last_year, db)

    # 2) 데이터 COPY
    copy_sql = text(f"""
        INSERT INTO {archive_table} (
            id, employee_id, client_id, product_id,
            quantity, return_amount, subsidy_amount,
            total_amount, sale_datetime
        )
        SELECT id, employee_id, client_id, product_id,
               quantity, return_amount, subsidy_amount,
               total_amount, sale_datetime
        FROM sales_records
        WHERE strftime('%Y', sale_datetime) = :year_str
    """)
    db.execute(copy_sql, {"year_str": str(last_year)})

    # 3) 원본에서 제거해 용량 확보
    delete_sql = text("""
        DELETE FROM sales_records
        WHERE strftime('%Y', sale_datetime) = :year_str
    """)
    db.execute(delete_sql, {"year_str": str(last_year)})

    db.commit()
    print(f"✅ {last_year}년 데이터 {archive_table}로 이관 완료")

def create_orders_archive_tables(year: int, db: Session):
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS orders_{year}        AS SELECT * FROM orders        WHERE 0;
        CREATE TABLE IF NOT EXISTS order_items_{year}   AS SELECT * FROM order_items   WHERE 0;
    """))
    db.commit()
    print(f"✅ orders·order_items {year} 테이블 생성")

def archive_orders_for_year_if_not_archived(year: int, db: Session):
    if db.execute(text(
        "SELECT name FROM sqlite_master WHERE name=:t"),
        {"t": f"orders_{year}"}
    ).first():
        print(f"⏩ 이미 아카이빙 완료 ({year})");  return

    create_orders_archive_tables(year, db)

    # 데이터 이관 (bulk insert → 속도 저하 없음)
    db.execute(text(f"""
        INSERT INTO orders_{year}      SELECT * FROM orders
        WHERE strftime('%Y', order_date) = :yr;
        INSERT INTO order_items_{year} SELECT oi.*
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        WHERE strftime('%Y', o.order_date) = :yr;
        DELETE FROM order_items
        WHERE id IN (SELECT id FROM order_items_{year});
        DELETE FROM orders WHERE strftime('%Y', order_date) = :yr;
    """), {"yr": str(year)})
    db.commit()
    print(f"📦 orders {year} 이관 완료")
