# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.payments import Payment
from app.schemas.payments import PaymentCreate, PaymentOut
from typing import List
from app.utils.time_utils import get_kst_now, get_kst_today, convert_utc_to_kst 
from app.models.sales_records import SalesRecord
from app.models.orders import Order, OrderItem
from typing import Dict
from app.models.products import Product
from app.models.employees import Employee
router = APIRouter()

@router.post("/", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    """
    새로운 결제(급여) 기록 추가 (KST 적용)
    """
    new_payment = Payment(
        client_id=payload.client_id,
        payment_date=payload.payment_date if payload.payment_date else get_kst_now(),  # ✅ KST 적용
        amount=payload.amount,
        payment_method=payload.payment_method,
        note=payload.note
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return convert_payment_to_kst(new_payment)  # ✅ KST 변환 후 반환

@router.get("/", response_model=List[PaymentOut])
def list_payments(db: Session = Depends(get_db)):
    """
    모든 결제(급여) 목록 조회 (KST 변환 적용)
    """
    payments = db.query(Payment).all()
    return [convert_payment_to_kst(payment) for payment in payments]  # ✅ KST 변환 적용

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    특정 급여 내역 조회 (KST 변환 적용)
    """
    payment = db.query(Payment).get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return convert_payment_to_kst(payment)  # ✅ KST 변환 적용

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

def convert_payment_to_kst(payment: Payment):
    """
    Payment 객체의 날짜/시간 필드를 KST로 변환하여 반환
    """
    return {
        "id": payment.id,
        "client_id": payment.client_id,
        "payment_date": convert_utc_to_kst(payment.payment_date).strftime("%Y-%m-%d %H:%M:%S") if payment.payment_date else None,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "note": payment.note,
        "created_at": convert_utc_to_kst(payment.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": convert_utc_to_kst(payment.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
    }

@router.get("/salary/{year}/{month}")
def calculate_salary(year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 연/월의 직원별 월매출을 구한 뒤,
    { 직원명: 매출 } 형태로 반환 (KST 적용)
    """
    from sqlalchemy import func

    start_date = get_kst_today().replace(year=year, month=month, day=1)  # ✅ KST 적용
    end_date = get_kst_today().replace(year=year, month=month, day=31)   # ✅ KST 적용

    results = (
        db.query(
            Employee.name.label("emp_name"),
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .select_from(SalesRecord)
        .join(Employee, SalesRecord.employee_id == Employee.id)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.sale_date >= start_date)
        .filter(SalesRecord.sale_date <= end_date)
        .group_by(Employee.name)
        .all()
    )

    output = {row.emp_name: float(row.total_sales or 0) for row in results}
    return output

# app/routers/payments.py

@router.get("/salary/{year}/{month}")
def get_monthly_sales(year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 연도(year), 월(month) 기준:
    직원별 월매출(=SalesRecord에 의한 총 매출액) 을 Dict[str, float] 형태로 반환
    예: { "김직원": 500000.0, "박직원": 350000.0, ... }
    """
    from sqlalchemy import func
    from datetime import date
    start_date = date(year, month, 1)
    # 실제론 month가 12일 때 날짜 계산 필요하지만, 예시로 31일 fixed
    end_date = date(year, month, 31)

    employees = db.query(Employee).all()
    result = {}

    for emp in employees:
        # 간단히 SalesRecord만 합산(단가 * 수량)
        total = (
            db.query(
                func.sum(Product.default_price * SalesRecord.quantity)
            )
            .join(Product, SalesRecord.product_id == Product.id)
            .filter(SalesRecord.employee_id == emp.id)
            .filter(SalesRecord.sale_date >= start_date, SalesRecord.sale_date <= end_date)
            .scalar()
        )
        result[emp.name] = float(total or 0.0)

    return result
