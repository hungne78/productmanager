# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.payments import Payment
from app.schemas.payments import PaymentCreate, PaymentOut
from typing import List

from app.models.sales_records import SalesRecord
from app.models.orders import Order, OrderItem
from typing import Dict
from app.models.products import Product
from app.models.employees import Employee
from sqlalchemy import extract, func
router = APIRouter()

@router.post("/", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    """ 새로운 결제 기록 추가 (KST로 저장) """
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
    return new_payment  # ✅ 변환 없이 그대로 반환

@router.get("/", response_model=List[PaymentOut])
def list_payments(db: Session = Depends(get_db)):
    """ 모든 결제 목록 조회 (KST 그대로 반환) """
    return db.query(Payment).all()  # ✅ 변환 없이 그대로 반환

@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """ 특정 결제 내역 조회 (KST 변환 없음) """
    payment = db.query(Payment).get(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment  # ✅ 변환 없이 그대로 반환

@router.put("/{payment_id}", response_model=PaymentOut)
def update_payment(payment_id: int, payload: PaymentCreate, db: Session = Depends(get_db)):
    """ 특정 결제 내역 수정 """
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
    return payment  # ✅ 변환 없이 그대로 반환

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

@router.get("/salary/{year}/{month}")
def calculate_salary(year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 연/월의 직원별 월매출을 구한 뒤,
    { 직원명: 매출 } 형태로 반환
    """
    from sqlalchemy import extract, func

    start_date = f"{year}-{int(month):02d}-01"
    end_date   = f"{year}-{int(month):02d}-31"

    # SalesRecord + Product 조인 → (Product.default_price * SalesRecord.quantity)
    # 직원(employee_id)별 sum()
    results = (
        db.query(
            Employee.name.label("emp_name"),
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        # 기준이 되는 메인 테이블을 명시적으로 잡아줌:
        .select_from(SalesRecord)
        # SalesRecord → Employee
        .join(Employee, SalesRecord.employee_id == Employee.id)
        # SalesRecord → Product
        .join(Product, SalesRecord.product_id == Product.id)
        # 날짜 필터
        .filter(SalesRecord.sale_datetime >= start_date)
        .filter(SalesRecord.sale_datetime <= end_date)
        # 직원명으로 그룹
        .group_by(Employee.name)
        .all()
    )

    # { 직원명: 매출 } 형태로 변환
    output = {}
    for row in results:
        emp_name = row.emp_name
        total_amt = float(row.total_sales or 0)
        output[emp_name] = total_amt

    return output


# app/routers/payments.py

@router.get("/salary/{year}/{month}")
def get_monthly_sales(year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 연도(year), 월(month) 기준:
    직원별 월매출(=SalesRecord에 의한 총 매출액) 을 Dict[str, float] 형태로 반환
    예: { "김승태": 500000.0, "한종현": 350000.0, ... }
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

@router.get("/salary_summary/{year}/{month}")
def get_salary_summary(year: int, month: int, db: Session = Depends(get_db)) -> Dict[str, dict]:
    """
    직원별로 특정 월의 (월매출, 인센티브 합) 반환
    Order 테이블에 total_amount, total_incentive 있다고 가정
    반환 형태:
      {
        "김영업": {"monthly_sales": 500000, "monthly_incentive": 20000},
        "이사원": {"monthly_sales": 300000, "monthly_incentive": 10000},
        ...
      }
    """
    # 1) Order 테이블에서 employee_id별 (total_amount, total_incentive) 합
    results = (
        db.query(
            Order.employee_id.label("emp_id"),
            func.sum(Order.total_amount).label("sum_amount"),
            func.sum(Order.total_incentive).label("sum_incentive"),
        )
        .filter(extract("year", Order.order_date) == year)
        .filter(extract("month", Order.order_date) == month)
        .group_by(Order.employee_id)
        .all()
    )
    # { emp_id: (sum_amount, sum_incentive) }
    tmp_dict = {}
    for r in results:
        tmp_dict[r.emp_id] = {
            "monthly_sales": float(r.sum_amount or 0.0),
            "monthly_incentive": float(r.sum_incentive or 0.0),
        }

    # 2) emp_id → emp_name 매핑
    employees = db.query(Employee.id, Employee.name).all()
    emp_map = {x.id: x.name for x in employees}

    # 3) 최종 출력: { emp_name: {monthly_sales, monthly_incentive} }
    output = {}
    for emp_id, data in tmp_dict.items():
        emp_name = emp_map.get(emp_id, f"직원#{emp_id}")
        output[emp_name] = {
            "monthly_sales": data["monthly_sales"],
            "monthly_incentive": data["monthly_incentive"],
        }
    return output

@router.get("/incentives/{year}/{month}")
def get_monthly_incentives(year: int, month: int, db: Session = Depends(get_db)) -> Dict[str, float]:
    """
    특정 연도/월 기준, 'orders' 테이블에 저장된 직원별 total_incentive 합계를 반환
    예: { "김영업": 30000.0, "이사원": 15000.0, ... }
    """

    # 1) 쿼리: orders 테이블에서 (직원ID별) total_incentive SUM
    results = (
        db.query(
            Order.employee_id.label("emp_id"),
            func.sum(Order.total_incentive).label("sum_incentive")
        )
        .filter(extract("year", Order.order_date) == year)
        .filter(extract("month", Order.order_date) == month)
        .group_by(Order.employee_id)
        .all()
    )

    # 2) 직원 ID → 직원명 매핑
    #    employees 테이블에서 id, name 가져와 dict
    employees = db.query(Employee.id, Employee.name).all()
    emp_map = {e.id: e.name for e in employees}

    # 3) 결과를 {직원명: 인센티브합} 형태로 변환
    output = {}
    for row in results:
        emp_id = row.emp_id
        emp_name = emp_map.get(emp_id, f"직원#{emp_id}")
        total_incentive = float(row.sum_incentive or 0.0)
        output[emp_name] = total_incentive

    return output