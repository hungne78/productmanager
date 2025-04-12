from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.monthly_sales import MonthlySales
from app.schemas.monthly_sales import MonthlySalesCreate, MonthlySalesOut

router = APIRouter()

# 🔹 월간 데이터 추가 (관리자 업로드 용)
@router.post("/", response_model=MonthlySalesOut)
def create_monthly_sales(payload: MonthlySalesCreate, db: Session = Depends(get_db)):
    record = MonthlySales(**payload.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

# 🔹 모든 월간 데이터 조회
@router.get("/", response_model=List[MonthlySalesOut])
def list_all_monthly_sales(db: Session = Depends(get_db)):
    return db.query(MonthlySales).all()

# 🔹 거래처별 연도별 매출 조회
@router.get("/client/{client_id}/{year}", response_model=List[MonthlySalesOut])
def get_client_yearly_sales(client_id: int, year: int, db: Session = Depends(get_db)):
    return db.query(MonthlySales).filter(
        MonthlySales.client_id == client_id,
        MonthlySales.year == year
    ).all()

# 🔹 특정 직원의 연도별 월간 매출
@router.get("/employee/{employee_id}/{year}", response_model=List[MonthlySalesOut])
def get_employee_yearly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    return db.query(MonthlySales).filter(
        MonthlySales.employee_id == employee_id,
        MonthlySales.year == year
    ).all()
