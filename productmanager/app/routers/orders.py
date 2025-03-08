from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Order, OrderItem
from app.schemas.orders import OrderSchema, OrderCreateSchema, OrderSummarySchema
from typing import List

router = APIRouter()

# ✅ 1️⃣ 모든 주문 목록 조회
@router.get("/orders/", response_model=List[OrderSchema])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders

# ✅ 2️⃣ 특정 주문 조회
@router.get("/orders/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order

# ✅ 3️⃣ 주문 생성
@router.post("", response_model=OrderSchema)
def create_order(order_data: OrderCreateSchema, db: Session = Depends(get_db)):
    order = Order(
        employee_id=order_data.employee_id,
        order_date=order_data.order_date,
        total_amount=order_data.total_amount,
        total_incentive=order_data.incentive,
        total_boxes=order_data.total_boxes
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in order_data.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(order_item)

    db.commit()
    return order

# ✅ 4️⃣ 특정 직원의 특정 날짜 주문 목록 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}", response_model=List[OrderSchema])
def get_orders_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date
    ).all()
    if not orders:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")
    return orders

# ✅ 5️⃣ 특정 직원의 특정 날짜 주문한 품목과 수량 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}/items", response_model=List[dict])
def get_order_items_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    order_items = (
        db.query(OrderItem.product_id, OrderItem.quantity)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.employee_id == employee_id, Order.order_date == order_date)
        .all()
    )
    if not order_items:
        raise HTTPException(status_code=404, detail="해당 직원의 주문 항목이 없습니다.")

    return [{"product_id": item.product_id, "quantity": item.quantity} for item in order_items]

# ✅ 6️⃣ 특정 직원의 특정 날짜 주문 총합, 인센티브 합계, 총 박스 수량 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}/summary", response_model=OrderSummarySchema)
def get_order_summary_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")

    return {
        "total_amount": order.total_amount,
        "total_incentive": order.total_incentive,
        "total_boxes": order.total_boxes
    }
