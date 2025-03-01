# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.payments import Payment
from app.schemas.payments import PaymentCreate, PaymentOut
from typing import List
from app.models.employees import Employee
from app.models.sales_records import SalesRecord
from app.models.orders import Order, OrderItem
from typing import Dict
router = APIRouter()

@router.post("/", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    """
    새로운 결제(급여) 기록 추가
    """
    new_payment = Payment(
        client_id=payload.client_id,
        payment_date=payload.payment_date,
        amount=payload.amount,
        payment_method=payload.payment_method,
        note=payload.note
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@router.get("/", response_model=List[PaymentOut])
def list_payments(db: Session = Depends(get_db)):
    """
    모든 결제(급여) 목록 조회
    """
    return db.query(Payment).all()

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    특정 급여 내역 조회
    """
    payment = db.query(Payment).get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment

@router.put("/{payment_id}", response_model=PaymentOut)
def update_payment(payment_id: int, payload: PaymentCreate, db: Session = Depends(get_db)):
    """
    특정 급여 내역 수정
    """
    payment = db.query(Payment).get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    payment.client_id = payload.client_id
    payment.payment_date = payload.payment_date
    payment.amount = payload.amount
    payment.payment_method = payload.payment_method
    payment.note = payload.note

    db.commit()
    db.refresh(payment)
    return payment

@router.delete("/{payment_id}")
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    특정 급여 내역 삭제
    """
    payment = db.query(Payment).get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    db.delete(payment)
    db.commit()
    return {"detail": "Payment record deleted"}

@router.get("/salary/{year}/{month}", response_model=Dict[str, float])
def calculate_salary(year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 연도, 월의 직원 급여 계산 (비율은 UI에서 조정)
    """
    employees = db.query(Employee).all()
    salary_data = {}

    for emp in employees:
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"

        total_sales = db.query(SalesRecord).filter(
            SalesRecord.employee_id == emp.id,
            SalesRecord.sale_date.between(start_date, end_date)
        ).with_entities(SalesRecord.quantity * SalesRecord.unit_price).all()
        
        total_sales_amount = sum(row[0] for row in total_sales) if total_sales else 0

        total_incentive = db.query(OrderItem).join(Order).filter(
            Order.employee_id == emp.id,
            Order.order_date.between(start_date, end_date)
        ).with_entities(OrderItem.incentive).all()

        total_incentive_amount = sum(row[0] for row in total_incentive) if total_incentive else 0

        salary_data[emp.name] = round(total_sales_amount + total_incentive_amount, 2)

    return salary_data

