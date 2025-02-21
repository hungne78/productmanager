from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.sales_records import SalesRecord
from app.schemas.sales import SalesCreate, SalesOut
from datetime import date
from typing import List

router = APIRouter()

# ✅ 매출 등록
@router.post("/", response_model=SalesOut)
def create_sales_record(payload: SalesCreate, db: Session = Depends(get_db)):
    new_sales = SalesRecord(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        total_amount=payload.total_amount,
        sale_date=payload.sale_date
    )
    db.add(new_sales)
    db.commit()
    db.refresh(new_sales)
    return new_sales

# ✅ 전체 매출 목록 조회
@router.get("/", response_model=List[SalesOut])
def list_sales_records(db: Session = Depends(get_db)):
    return db.query(SalesRecord).all()

# ✅ 특정 직원의 매출 조회
@router.get("/employee/{employee_id}", response_model=List[SalesOut])
def get_sales_by_employee(employee_id: int, db: Session = Depends(get_db)):
    return db.query(SalesRecord).filter(SalesRecord.employee_id == employee_id).all()

# ✅ 특정 날짜의 매출 조회
@router.get("/date/{sale_date}", response_model=List[SalesOut])
def get_sales_by_date(sale_date: date, db: Session = Depends(get_db)):
    return db.query(SalesRecord).filter(SalesRecord.sale_date == sale_date).all()

# ✅ 매출 삭제
@router.delete("/{sales_id}")
def delete_sales_record(sales_id: int, db: Session = Depends(get_db)):
    sales = db.query(SalesRecord).get(sales_id)
    if not sales:
        raise HTTPException(status_code=404, detail="Sales record not found")
    db.delete(sales)
    db.commit()
    return {"detail": "Sales record deleted"}
