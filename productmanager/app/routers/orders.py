# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.orders import Order, OrderItem
from app.schemas.orders import (
    OrderCreate, OrderOut, OrderItemCreate
)

router = APIRouter()

@router.post("/", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    주문 생성
    """
    new_order = Order(
        client_id=payload.client_id,
        employee_id=payload.employee_id,
        status=payload.status if payload.status else "pending"
    )

    # order_date가 들어왔다면 적용
    if payload.order_date:
        new_order.order_date = payload.order_date

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    total_amount = 0.0
    # 주문 항목 생성
    for item_data in payload.items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=item_data.line_total,
            incentive=item_data.incentive
        )
        total_amount += item_data.line_total
        db.add(order_item)

    # 총액 업데이트
    new_order.total_amount = total_amount
    db.commit()
    db.refresh(new_order)

    return new_order


@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    """
    전체 주문 목록
    """
    orders = db.query(Order).all()
    return orders


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """
    특정 주문 조회
    """
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    """
    주문 삭제 (주문 아이템도 함께 삭제)
    """
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # order_items 삭제
    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return {"detail": "Order and items deleted"}


@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderCreate, db: Session = Depends(get_db)):
    """
    주문 수정 (간단 예시)
    - 기존 아이템 전부 삭제 후 새로 생성, 혹은 부분 업데이트 등은 상황에 맞게 구현
    """
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.client_id = payload.client_id
    order.employee_id = payload.employee_id
    order.status = payload.status if payload.status else order.status

    if payload.order_date:
        order.order_date = payload.order_date

    # 기존 아이템들 삭제(예시: all clear 후 다시 생성)
    db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

    total_amount = 0.0
    for item_data in payload.items:
        new_item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            line_total=item_data.line_total,
            incentive=item_data.incentive
        )
        total_amount += item_data.line_total
        db.add(new_item)

    order.total_amount = total_amount

    db.commit()
    db.refresh(order)
    return order

# ---------------------------------------------------------
# 추가 요구사항: 날짜 + 직원 검색
# ---------------------------------------------------------
@router.get("/search", response_model=List[OrderOut])
def search_orders(
    date_query: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """
    - date_query만 있으면: 해당 날짜의 모든 주문
    - date_query + employee_id 둘 다 있으면: 해당 날짜 + 해당 직원의 주문
    - 둘 다 없으면: 전체 주문
    """
    query = db.query(Order)

    # 날짜 필터
    if date_query:
        # order_date == date_query
        query = query.filter(Order.order_date == date_query)

    # 직원 필터
    if employee_id:
        query = query.filter(Order.employee_id == employee_id)

    orders = query.all()
    return orders
