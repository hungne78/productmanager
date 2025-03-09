from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Order, OrderItem
from app.schemas.orders import OrderSchema, OrderCreateSchema, OrderSummarySchema
from typing import List
from datetime import date
from sqlalchemy import Boolean, Column, Integer, Date
from app.models import Product
from app.db.base import Base

router = APIRouter()

# ✅ 1️⃣ 주문 종료 테이블 추가
class OrderLock(Base):
    __tablename__ = "order_locks"

    id = Column(Integer, primary_key=True, index=True)
    lock_date = Column(Date, unique=True, nullable=False)  # ✅ 차단할 날짜
    is_locked = Column(Boolean, default=True)  # ✅ 주문 차단 여부 (기본값: True)

# ✅ 2️⃣ 주문 종료 (관리자용)
@router.post("/orders/lock/{order_date}")
def lock_order_date(order_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 주문을 차단 (관리자용)
    """
    existing_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    
    if existing_lock:
        existing_lock.is_locked = True
    else:
        new_lock = OrderLock(lock_date=order_date, is_locked=True)
        db.add(new_lock)
    
    db.commit()
    return {"message": f"{order_date} 주문이 종료되었습니다."}


# ✅ 3️⃣ 주문 해제 (관리자용)
@router.post("/orders/unlock/{order_date}")
def unlock_order_date(order_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 주문 차단을 해제 (관리자용)
    """
    existing_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    
    if existing_lock:
        existing_lock.is_locked = False
        db.commit()
        return {"message": f"{order_date} 주문 차단이 해제되었습니다."}

    raise HTTPException(status_code=404, detail="해당 날짜의 주문 차단 기록이 없습니다.")


# ✅ 4️⃣ 특정 날짜가 차단되었는지 확인
@router.get("/orders/is_locked/{order_date}")
def is_order_locked(order_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 주문이 차단되었는지 확인
    """
    lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    return {"is_locked": lock.is_locked if lock else False}

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
        total_incentive=order_data.total_incentive,
        total_boxes=order_data.total_boxes
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item in order_data.order_items:
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
@router.get("/orders_with_items", response_model=List[dict])
def get_orders_with_items(employee_id: int, date: str, db: Session = Depends(get_db)):
    """
    특정 직원의 특정 날짜 주문과 해당 주문의 상품 항목을 함께 조회하는 API (품명 포함)
    """
    orders = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == date
    ).all()

    if not orders:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")

    result = []
    for order in orders:
        order_items = (
            db.query(OrderItem, Product.product_name)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(OrderItem.order_id == order.id)
            .all()
        )
        items = [{"product_id": item.OrderItem.product_id, "product_name": item.product_name, "quantity": item.OrderItem.quantity} for item in order_items]
        
        result.append({
            "order_id": order.id,
            "order_date": order.order_date,
            "total_amount": order.total_amount,
            "total_boxes": order.total_boxes,
            "items": items
        })

    return result
# ✅ 기존 주문 덮어쓰기 (UPSERT)
@router.post("/upsert", response_model=OrderSchema)
def create_or_update_order(order_data: OrderCreateSchema, db: Session = Depends(get_db)):
    """
    같은 날짜의 주문이 있으면 덮어쓰기 (UPSERT)
    """
    existing_order = (
        db.query(Order)
        .filter(Order.employee_id == order_data.employee_id)
        .filter(Order.order_date == order_data.order_date)
        .first()
    )

    if existing_order:
        # ✅ 기존 주문 삭제 후 다시 생성
        db.query(OrderItem).filter(OrderItem.order_id == existing_order.id).delete()
        db.delete(existing_order)
        db.commit()

    # ✅ 새 주문 생성
    new_order = Order(
        employee_id=order_data.employee_id,
        order_date=order_data.order_date,
        total_amount=order_data.total_amount,
        total_incentive=order_data.total_incentive,
        total_boxes=order_data.total_boxes,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # ✅ 주문 항목 추가
    for item in order_data.order_items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    db.commit()
    return new_order

@router.put("/orders/update_quantity/")
def update_order_quantity(
    employee_id: int, order_date: str, product_id: int, data: dict, db: Session = Depends(get_db)
):
    """
    특정 날짜, 특정 직원이 주문한 특정 상품의 주문 수량을 수정
    """
    new_quantity = data.get("quantity")
    if new_quantity is None or not isinstance(new_quantity, int) or new_quantity < 0:
        raise HTTPException(status_code=400, detail="유효한 수량(quantity)이 필요합니다.")

    # ✅ 특정 날짜, 특정 직원이 주문한 Order 찾기
    order = (
        db.query(Order)
        .filter(Order.employee_id == employee_id, Order.order_date == order_date)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")

    # ✅ OrderItem에서 해당 상품 찾기
    order_item = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id, OrderItem.product_id == product_id)
        .first()
    )

    if not order_item:
        raise HTTPException(status_code=404, detail="주문 내역에서 해당 상품을 찾을 수 없습니다.")

    # ✅ 주문 수량 업데이트
    order_item.quantity = new_quantity
    db.commit()
    db.refresh(order_item)

    return {"message": "주문 수량이 성공적으로 업데이트되었습니다.", "order_id": order.id, "product_id": product_id, "new_quantity": new_quantity}
