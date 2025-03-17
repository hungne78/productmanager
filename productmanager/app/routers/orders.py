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
from app.models.orders import OrderLock
from sqlalchemy import func
router = APIRouter()



# ✅ 1️⃣ 주문 잠금 (관리자용)
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

# ✅ 2️⃣ 주문 해제 (관리자용)
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

@router.get("/lock_status/{order_date}")
def check_order_lock_status(order_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 주문이 잠겨있는지 및 출고 확정되었는지 확인
    """
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()

    if not order_lock:
        return {"order_date": order_date, "is_locked": False, "is_finalized": False}

    return {
        "order_date": order_date,
        "is_locked": order_lock.is_locked,
        "is_finalized": order_lock.is_finalized
    }

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

    # ✅ 주문이 잠겨 있는지 확인
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_data.order_date).first()
    if order_lock and order_lock.is_locked:
        raise HTTPException(status_code=403, detail="이 날짜의 주문은 수정이 불가능합니다.")

    # ✅ 수량이 음수인지 확인 (0 이상만 허용)
    for item in order_data.order_items:
        if item.quantity < 0:
            raise HTTPException(status_code=400, detail=f"상품 {item.product_id}의 수량이 유효하지 않습니다. (0 이상 필요)")

    # ✅ 현재 출고 단계 조회 (출고 단계가 없으면 기본값 0 설정)
    last_shipment_round = (
        db.query(func.max(Order.shipment_round))
        .filter(Order.order_date == order_data.order_date)
        .scalar()
    ) or 0  # ✅ None이면 0으로 설정

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
        existing_order.shipment_round = last_shipment_round  # ✅ 출고 단계 유지

        # ✅ 기존 주문 항목 조회 및 매핑
        existing_order_items = db.query(OrderItem).filter(OrderItem.order_id == existing_order.id).all()
        existing_order_map = {item.product_id: item.quantity for item in existing_order_items}

        # ✅ 출고된 내역이 있는지 확인하여 변경 불가하도록 설정
        for item in order_data.order_items:
            if item.product_id in existing_order_map:
                if existing_order.shipment_round > last_shipment_round:
                    # ✅ 이미 출고된 상품은 수량 변경 불가
                    raise HTTPException(status_code=400, detail=f"상품 {item.product_id}은(는) 이미 출고되어 수정할 수 없습니다.")

                # ✅ 기존 주문이 있으면 수량만 업데이트 (출고되지 않은 경우)
                db.query(OrderItem).filter(
                    OrderItem.order_id == existing_order.id,
                    OrderItem.product_id == item.product_id
                ).update({"quantity": item.quantity})
            else:
                # ✅ 기존에 없던 제품이면 새로 추가
                db.add(OrderItem(order_id=existing_order.id, product_id=item.product_id, quantity=item.quantity))

        db.commit()
        db.refresh(existing_order)

        print(f"✅ [디버깅] 주문 수정 완료 - 차량 재고 업데이트 호출")
        update_vehicle_stock(order_data.employee_id, db)  # ✅ 차량 재고 업데이트 호출

        return existing_order

    # ✅ 기존 주문이 없으면 새 주문 생성
    new_order = Order(
        employee_id=order_data.employee_id,
        order_date=order_data.order_date,
        total_amount=order_data.total_amount,
        total_incentive=order_data.total_incentive,
        total_boxes=order_data.total_boxes,
        shipment_round=last_shipment_round  # ✅ 출고 단계 유지
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # ✅ 새 주문 항목 추가
    for item in order_data.order_items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    db.commit()

    print(f"✅ [디버깅] 새 주문 생성 완료 - 차량 재고 업데이트 호출")
    update_vehicle_stock(order_data.employee_id, db)  # ✅ 차량 재고 업데이트 호출

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

# ✅ 기존 주문 덮어쓰기 (UPSERT)
@router.post("/orders/", response_model=OrderSchema)
def create_or_update_order(order_data: OrderCreateSchema, db: Session = Depends(get_db), is_archive: bool = Query(False)):
    """
    직원 ID와 주문 날짜가 같은 주문이 있으면 업데이트, 없으면 새 주문 생성
    (is_archive=True면 아카이빙 테이블에 추가)
    """
    table = OrderArchive if is_archive else Order

    # ✅ 기존 주문 조회
    existing_order = (
        db.query(table)
        .filter(table.employee_id == order_data.employee_id)
        .filter(table.order_date == order_data.order_date)
        .first()
    )

    if existing_order:
        # ✅ 기존 주문이 있다면 업데이트
        existing_order.total_amount = order_data.total_amount
        existing_order.total_incentive = order_data.total_incentive
        existing_order.total_boxes = order_data.total_boxes

        # ✅ 기존 주문 항목을 삭제하지 않고 업데이트
        for item in order_data.order_items:
            existing_order_item = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == existing_order.id, OrderItem.product_id == item.product_id)
                .first()
            )
            if existing_order_item:
                existing_order_item.quantity = item.quantity  # ✅ 기존 데이터 업데이트
            else:
                db.add(OrderItem(order_id=existing_order.id, product_id=item.product_id, quantity=item.quantity))

        db.commit()
        db.refresh(existing_order)

        print(f"✅ [디버깅] 주문 수정 완료 - 차량 재고 업데이트 ❌ (출고 확정 시 업데이트됨)")

        return existing_order

    # ✅ 기존 주문이 없으면 새 주문 생성
    new_order = table(
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
        db.add((OrderItem if not is_archive else OrderItemArchive)(
            order_id=new_order.id, product_id=item.product_id, quantity=item.quantity
        ))

    db.commit()
    return new_order



from fastapi import Body

@router.put("/update_quantity/{order_id}/")
def update_order_quantity(
    order_id: int, 
    order_date: date, 
    quantity: int = Body(..., embed=True),  # ✅ Body 객체 사용
    is_admin: bool = Query(False, description="관리자 여부"), 
    db: Session = Depends(get_db)
):
    """
    특정 주문 항목의 수량을 수정 (주문이 잠겨있으면 수정 불가)
    """
    # ✅ 주문이 잠겨있는지 확인
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    if order_lock and order_lock.is_locked and not is_admin:
        raise HTTPException(status_code=403, detail="이 날짜의 주문은 수정이 불가능합니다.")

    # ✅ 해당 주문 항목 가져오기
    order_item = db.query(OrderItem).filter(OrderItem.id == order_id).first()
    if not order_item:
        raise HTTPException(status_code=404, detail="해당 주문 항목을 찾을 수 없습니다.")

    # ✅ 주문 수량 업데이트
    order_item.quantity = quantity
    db.commit()
    return {"message": "주문 수량이 수정되었습니다.", "order_id": order_id, "quantity": quantity}

@router.get("/current_shipment_round/{order_date}")
def get_current_shipment_round(order_date: date, db: Session = Depends(get_db)):
    """
    현재 날짜의 마지막 출고 단계를 반환
    """
    last_shipment_round = db.query(func.max(Order.shipment_round)).filter(
        Order.order_date == order_date
    ).scalar() or 0

    return {"order_date": order_date, "shipment_round": last_shipment_round}