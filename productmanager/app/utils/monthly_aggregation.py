# app/utils/monthly_aggregation.py

from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime
from app.models.sales_records import SalesRecord
from app.models.monthly_sales import MonthlySales
from app.models.products import Product

def aggregate_sales_to_monthly(db: Session, year: int, month: int):
    """ sales_records → monthly_sales 로 집계 """

    # 중복 방지: 기존 데이터 삭제
    db.query(MonthlySales).filter(
        MonthlySales.year == year,
        MonthlySales.month == month
    ).delete()

    # 집계 쿼리 실행
    results = (
        db.query(
            SalesRecord.client_id,
            SalesRecord.employee_id,
            func.sum(SalesRecord.quantity * Product.default_price).label("total_sales"),
            func.sum(SalesRecord.return_amount).label("total_returns"),
            func.sum(SalesRecord.subsidy_amount).label("total_subsidy")
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(extract("year", SalesRecord.sale_datetime) == year)
        .filter(extract("month", SalesRecord.sale_datetime) == month)
        .group_by(SalesRecord.client_id, SalesRecord.employee_id)
        .all()
    )

    for row in results:
        db.add(MonthlySales(
            client_id=row.client_id,
            employee_id=row.employee_id,
            year=year,
            month=month,
            total_sales=row.total_sales or 0.0,
            total_returns=row.total_returns or 0.0,
            total_subsidy=row.total_subsidy or 0.0,
        ))
    
    db.commit()
    print(f"📊 [집계 완료] {year}-{month} 매출 {len(results)}건 저장됨.")
