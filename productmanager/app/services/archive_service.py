from sqlalchemy.orm import Session
from datetime import datetime
from app.models.sales_records import SalesRecord
from app.utils.archive_utils import create_archive_table_if_not_exists
from sqlalchemy import extract, text

def archive_sales_for_year(year: int, db: Session):
    # 1. 아카이브 테이블 생성
    create_archive_table_if_not_exists(year, db)
    
    table_name = f"sales_records_{year}"

    # 2. INSERT
    insert_sql = text(f"""
        INSERT INTO {table_name}
        SELECT * FROM sales_records
        WHERE YEAR(sale_datetime) = :year
    """)
    db.execute(insert_sql, {"year": year})
    db.commit()
    print(f"📤 {year}년 데이터 아카이브 완료 (INSERT)")

    # 3. DELETE
    delete_q = (
        db.query(SalesRecord)
        .filter(extract("year", SalesRecord.sale_datetime) == year)
    )
    deleted = delete_q.delete(synchronize_session=False)
    db.commit()
    print(f"🧹 {year}년 데이터 삭제 완료 (DELETE {deleted}건)")
