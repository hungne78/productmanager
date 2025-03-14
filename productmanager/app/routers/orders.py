from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Order, OrderItem, OrderArchive, OrderItemArchive  # ✅ 아카이빙 테이블 추가
from app.schemas.orders import OrderSchema, OrderCreateSchema, OrderSummarySchema
from typing import List
from datetime import date
from sqlalchemy import Boolean, Column, Integer, Date
from app.models import Product
from app.db.base import Base
from fastapi.responses import JSONResponse
from app.utils.inventory_service import update_vehicle_stock
router = APIRouter()

# ✅ 1️⃣ 주문 종료 테이블 추가
class OrderLock(Base):
    __tablename__ = "order_locks"

    id = Column(Integer, primary_key=True, index=True)
    lock_date = Column(Date, unique=True, nullable=False)  # ✅ 차단할 날짜
    is_locked = Column(Boolean, default=True)  # ✅ 주문 차단 여부 (기본값: True)

# ✅ 2️⃣ 주문 종료 (관리자용)
@router.post("/lock/{order_date}")
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
@router.post("/unlock/{order_date}")
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

# ✅ 공통 함수: 특정 테이블에서 주문 데이터 가져오기
def get_orders_from_table(db: Session, table):
    orders = db.query(table).all()
    if not orders:
        raise HTTPException(status_code=404, detail="데이터가 없습니다.")
    return orders

# ✅ 1️⃣ 모든 주문 목록 조회
@router.get("/orders/", response_model=List[OrderSchema])
def get_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return orders

# ✅ 2️⃣ 한 달 이상 지난 주문 조회 (orders_archive 테이블)
@router.get("/orders_archive", response_model=List[OrderSchema])
def get_archived_orders(db: Session = Depends(get_db)):
    """ 한 달 이상 지난 주문 목록 조회 """
    return get_orders_from_table(db, OrderArchive)

# ✅ 3️⃣ 특정 주문 조회 (현재 주문 + 아카이빙 주문 지원)
@router.get("/orders/{order_id}", response_model=OrderSchema)
@router.get("/orders_archive/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db), is_archive: bool = Query(False)):
    """ 특정 주문 조회 (is_archive=True면 아카이빙 테이블에서 조회) """
    table = OrderArchive if is_archive else Order
    order = db.query(table).filter(table.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order

@router.post("/", response_model=OrderSchema)
def create_or_update_order(order_data: OrderCreateSchema, db: Session = Depends(get_db)):
    """
    직원 ID와 주문 날짜가 같은 주문이 있으면 업데이트, 없으면 새 주문 생성
    주문 완료 후 차량 재고를 자동 업데이트
    """
    today = date.today()

    # ✅ 기존 주문 조회 (같은 직원 & 같은 날짜)
    existing_order = (
        db.query(Order)
        .filter(Order.employee_id == order_data.employee_id)
        .filter(Order.order_date == order_data.order_date)
        .first()
    )

    if existing_order:
        # ✅ 기존 주문이 있다면 업데이트
        existing_order.total_amount = order_data.total_amount
        existing_order.total_incentive = order_data.total_incentive
        existing_order.total_boxes = order_data.total_boxes

        # ✅ 기존 주문 항목 조회
        existing_items = {
            item.product_id: item for item in db.query(OrderItem)
            .filter(OrderItem.order_id == existing_order.id)
            .all()
        }

        # ✅ 새 주문 항목 처리 (수량 업데이트 또는 새로 추가)
        for item in order_data.order_items:
            if item.product_id in existing_items:
                # ✅ 기존 제품이 있으면 수량 업데이트
                existing_items[item.product_id].quantity = item.quantity
            else:
                # ✅ 새 제품이면 추가
                db.add(OrderItem(order_id=existing_order.id, product_id=item.product_id, quantity=item.quantity))

        db.commit()
        db.refresh(existing_order)

        # ✅ 차량 재고 자동 업데이트 호출
        update_vehicle_stock(order_data.employee_id, db)

        return existing_order

    # ✅ 기존 주문이 없으면 새 주문 생성
    new_order = Order(
        employee_id=order_data.employee_id,
        order_date=order_data.order_date,
        total_amount=order_data.total_amount,
        total_incentive=order_data.total_incentive,
        total_boxes=order_data.total_boxes
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # ✅ 새 주문 항목 추가
    for item in order_data.order_items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    db.commit()

    # ✅ 차량 재고 자동 업데이트 호출
    update_vehicle_stock(order_data.employee_id, db)

    return new_order




# ✅ 4️⃣ 특정 직원의 특정 날짜 주문 목록 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}", response_model=List[OrderSchema])
@router.get("/orders_archive/employee/{employee_id}/date/{order_date}", response_model=List[OrderSchema])
def get_orders_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db), is_archive: bool = Query(False)):
    """
    특정 직원의 특정 날짜 주문 목록 조회 (is_archive=True면 아카이빙 테이블에서 조회)
    """
    table = OrderArchive if is_archive else Order
    orders = db.query(table).filter(
        table.employee_id == employee_id,
        table.order_date == order_date
    ).all()

    if not orders:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")
    return orders




@router.get("/employee/{employee_id}/date/{order_date}/items", response_model=List[dict])
def get_order_items_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.employee_id == employee_id, Order.order_date == order_date).first()
    if not order:
        print(f"❌ [FastAPI] 주문 내역 없음 (직원 ID: {employee_id}, 날짜: {order_date})")
        return JSONResponse(content=[], status_code=200, media_type="application/json; charset=utf-8")

    order_items = (
        db.query(
            OrderItem.product_id,
            OrderItem.quantity,
            Product.product_name,
            Product.category,
            Product.brand_id
        )
        .join(Product, Product.id == OrderItem.product_id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    print(f"✅ [FastAPI] {len(order_items)}개 주문 항목 조회됨")

    # ✅ 조회된 데이터 확인
    for item in order_items:
        print(f"🔍 상품 ID: {item.product_id}, 상품명: {item.product_name}, 카테고리: {item.category}, 브랜드 ID: {item.brand_id}")

    formatted_result = {
        "total_amount": order.total_amount,
        "total_incentive": order.total_incentive,
        "total_boxes": order.total_boxes,
        "items": []
    }

    category_brand_dict = {}

    for item in order_items:
        category = item.category or "기타"
        brand_id = item.brand_id or 0  

        if category not in category_brand_dict:
            category_brand_dict[category] = {}

        if brand_id not in category_brand_dict[category]:
            category_brand_dict[category][brand_id] = []

        category_brand_dict[category][brand_id].append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product_name": item.product_name or "상품 정보 없음",
        })

    # ✅ `List[dict]`로 변환하여 FastAPI 응답 형식과 맞춤
    for category, brands in category_brand_dict.items():
        for brand_id, products in brands.items():
            formatted_result["items"].append({
                "category": category,
                "brand_id": brand_id,
                "products": products
            })

    return JSONResponse(content=formatted_result, media_type="application/json; charset=utf-8")



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


@router.put("/update_quantity/{product_id}/")
def update_order_quantity(
    product_id: int,
    order_date: str = Query(...),  # ✅ 선택한 날짜를 query parameter로 받음
    data: dict = Body(...),  # ✅ 수량은 request body에서 받음
    db: Session = Depends(get_db)
):
    """
    특정 날짜에 주문된 특정 상품의 주문 수량을 수정
    """
    new_quantity = data.get("quantity")
    if new_quantity is None or not isinstance(new_quantity, int) or new_quantity < 0:
        raise HTTPException(status_code=400, detail="유효한 수량(quantity)이 필요합니다.")

    # ✅ 특정 날짜의 주문 중 해당 상품을 포함한 주문 찾기
    order_item = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.order_date == order_date, OrderItem.product_id == product_id)
        .first()
    )

    if not order_item:
        raise HTTPException(status_code=404, detail="해당 날짜에 주문된 해당 상품을 찾을 수 없습니다.")

    # ✅ 주문 수량 업데이트
    order_item.quantity = new_quantity
    db.commit()
    db.refresh(order_item)

    return {
        "message": "주문 수량이 성공적으로 업데이트되었습니다.",
        "order_id": order_item.order_id,
        "product_id": product_id,
        "new_quantity": new_quantity
    }
