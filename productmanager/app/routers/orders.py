from fastapi import APIRouter, Depends, HTTPException, Body, Query, WebSocket
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
from typing import Optional
from datetime import datetime
from app.models import Brand  # 브랜드 모델 import
import pytz
import redis
from pathlib import Path
import json
from functools import lru_cache
from sqlalchemy import Table
from app.db.base import Base, engine        # ✅ Base(metadata 포함)·engine 만 가져오면 충분
from sqlalchemy import extract
# Base.metadata 그대로 사용
metadata = Base.metadata

# --------------------------------------------------
# 0.  YEAR‑파티션 테이블용 동적 모델 팩토리
# --------------------------------------------------
@lru_cache(maxsize=None)
def get_order_model(year: int):
    """
    - 올해(year==현재년도) → 기존 Order 모델 그대로 반환
    - 과거/미래 연도       → order_YYYY 테이블을 리플렉션해
                            SQLAlchemy 모델 클래스를 즉석 생성 후 반환
    """
    from app.models.orders import Order            # 순환 import 방지

    if year == datetime.now().year:
        return Order

    table_name = f"order_{year}"
    if table_name in Base.registry._class_registry:      # 이미 만들어 둔 모델이면 재사용
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)

    return type(f"Order{year}", (Base,), {
        "__table__":   tbl,
        "__tablename__": table_name,
    })


@lru_cache(maxsize=None)
def get_order_item_model(year: int):
    """OrderItem 파티션 테이블용 동적 모델"""
    from app.models.orders import OrderItem

    if year == datetime.now().year:
        return OrderItem

    table_name = f"orderitem_{year}"
    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)

    return type(f"OrderItem{year}", (Base,), {
        "__table__":   tbl,
        "__tablename__": table_name,
    })

router = APIRouter()

# ✅ Redis 설정
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# ✅ WebSocket 연결 관리
active_websockets = []

BASE_DIR = Path(__file__).resolve().parent.parent.parent


@router.get("/category")
def get_category_order():
    file = BASE_DIR / "category_order_server.json"
    return json.load(open(file, encoding="utf-8"))

@router.get("/brand")
def get_brand_order():
    file = BASE_DIR / "brand_order_server.json"
    return json.load(open(file, encoding="utf-8"))


@router.get("/server-time")
def get_server_time():
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    return {
        "server_time": now.isoformat()
    }

@router.get("/warehouse_stock")
def get_warehouse_stock(db: Session = Depends(get_db)):
    """
    Redis에서 창고 재고 조회 (없으면 DB에서 조회 후 캐싱)
    """
    cache_data = redis_client.get("warehouse_stock")

    if cache_data:
        return json.loads(cache_data)  # ✅ Redis 캐시에서 재고 반환

    # ✅ Redis에 없으면 DB에서 조회 후 캐싱
    products = db.query(Product.id, Product.product_name, Product.stock).all()
    result = [{"product_id": p.id, "product_name": p.product_name, "quantity": p.stock} for p in products]

    redis_client.setex("warehouse_stock", 60, json.dumps(result))  # ✅ 60초 캐싱
    return result

@router.get("/exists/{order_date}")
def check_first_order(order_date: date, db: Session = Depends(get_db)):
    """
    해당 날짜(order_date)에 *실제 상품이 들어있는 주문* 이 존재하는지 확인  
    (연도별 파티션 테이블 자동 선택)
    """
    y = order_date.year
    Order      = get_order_model(y)
    OrderItem  = get_order_item_model(y)

    cnt = (
        db.query(Order)
          .join(OrderItem, Order.id == OrderItem.order_id)
          .filter(Order.order_date == order_date)
          .count()
    )
    return {"exists": cnt > 0}
@router.post("/place_order")
def place_order(order_items: List[dict], db: Session = Depends(get_db)):
    """
    트랜잭션과 락을 사용하여 동시 주문 문제 해결
    """
    try:
        db.begin()  # ✅ 트랜잭션 시작

        for item in order_items:
            product = db.query(Product).filter(Product.id == item['product_id']).with_for_update().first()

            if not product or product.stock < item['quantity']:
                raise HTTPException(status_code=400, detail=f"{product.product_name} 재고 부족")

            product.stock -= item['quantity']

            # ✅ Redis 개별 캐시 업데이트
            redis_client.set(f"product_{product.id}_stock", product.stock)

        db.commit()

        # ✅ Kafka 대신 Redis Pub/Sub로 주문 메시지 발행
        redis_client.publish("order_topic", json.dumps({"order_items": order_items}))

        # ✅ WebSocket 클라이언트에게 실시간 재고 알림
        notify_clients()

        return {"message": "주문 성공!"}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="🚨 주문 처리 중 오류 발생!")

# ✅ WebSocket을 통한 실시간 재고 업데이트
async def notify_clients():
    data = {"message": "재고 업데이트됨"}
    for websocket in active_websockets:
        await websocket.send_text(json.dumps(data))

@router.websocket("/ws/stock_updates")
async def stock_websocket(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_websockets.remove(websocket)

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
def get_orders(year: int = Query(None), db: Session = Depends(get_db)):
    year = year or datetime.now().year
    Order = get_order_model(year)
    orders = db.query(Order).all()
    return orders


# ✅ 2️⃣ 한 달 이상 지난 주문 조회 (orders_archive 테이블)
@router.get("/orders_archive", response_model=List[OrderSchema])
def get_archived_orders(db: Session = Depends(get_db)):
    """ 한 달 이상 지난 주문 목록 조회 """
    return get_orders_from_table(db, OrderArchive)

@router.get("/orders/{order_id}", response_model=OrderSchema)
@router.get("/orders_archive/{order_id}", response_model=OrderSchema)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    year: int = Query(None),
    is_archive: bool = Query(False)
):
    if is_archive:
        table = OrderArchive
    else:
        year = year or datetime.now().year
        table = get_order_model(year)

    order = db.query(table).filter(table.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order



from sqlalchemy.sql import exists
@router.post("/", response_model=OrderSchema)
def create_or_update_order(order_data: OrderCreateSchema, db: Session = Depends(get_db)):
    """
    주문 생성 또는 업데이트 (출고 차수 검증 + 창고 재고 차감)
    출고 차수는 PC에서 확정 버튼 눌러야 올라감
    """
    order_year = order_data.order_date.year
    Order = get_order_model(order_year)
    OrderItem = get_order_item_model(order_year)

    today = date.today()

    # ✅ 현재 출고 차수 조회
    last_shipment_round = (
        db.query(func.max(Order.shipment_round))
        .filter(Order.order_date == order_data.order_date)
        .scalar()
    ) or 0

    if order_data.shipment_round > last_shipment_round:
        raise HTTPException(status_code=400, detail=f"출고 차수가 유효하지 않습니다. (현재: {last_shipment_round})")

    # ✅ 중복 주문 차단
    order_item_count = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.employee_id == order_data.employee_id)
        .filter(Order.order_date == order_data.order_date)
        .filter(Order.shipment_round == order_data.shipment_round)
        .count()
    )
    if order_item_count > 0:
        raise HTTPException(status_code=403, detail="이 차수에 대해 이미 주문이 전송되었습니다.")

    # ✅ 잠금 여부 확인
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_data.order_date).first()
    if order_lock and order_lock.is_locked:
        raise HTTPException(status_code=403, detail="이 날짜의 주문은 잠겨 있습니다.")

    # ✅ 기존 주문 확인
    existing_order = (
        db.query(Order)
        .filter(Order.employee_id == order_data.employee_id)
        .filter(Order.order_date == order_data.order_date)
        .filter(Order.shipment_round == order_data.shipment_round)
        .first()
    )

    if existing_order:
        # ✅ 출고된 차수는 수정 금지
        if existing_order.shipment_round < last_shipment_round:
            raise HTTPException(status_code=400, detail="이미 출고된 주문은 수정할 수 없습니다.")

        # ✅ 기존 주문 수정
        existing_order.total_amount = order_data.total_amount
        existing_order.total_incentive = order_data.total_incentive
        existing_order.total_boxes = order_data.total_boxes

        existing_items = db.query(OrderItem).filter(OrderItem.order_id == existing_order.id).all()
        existing_map = {item.product_id: item.quantity for item in existing_items}

        for item in order_data.order_items:
            product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"상품 {item.product_id} 없음")

            new_q = item.quantity
            old_q = existing_map.get(item.product_id, 0)
            diff = new_q - old_q

            if diff > 0:
                if product.stock < diff:
                    raise HTTPException(status_code=400, detail=f"{product.product_name} 재고 부족")
                product.stock -= diff
            elif diff < 0:
                product.stock += abs(diff)

            if item.product_id in existing_map:
                db.query(OrderItem).filter(
                    OrderItem.order_id == existing_order.id,
                    OrderItem.product_id == item.product_id
                ).update({"quantity": new_q})
            else:
                db.add(OrderItem(order_id=existing_order.id, product_id=item.product_id, quantity=new_q))

        db.commit()
        db.refresh(existing_order)
        return existing_order

    # ✅ 신규 주문 생성
    new_order = Order(
        employee_id=order_data.employee_id,
        order_date=order_data.order_date,
        shipment_round=order_data.shipment_round,
        total_amount=order_data.total_amount,
        total_incentive=order_data.total_incentive,
        total_boxes=order_data.total_boxes
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order_data.order_items:
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail=f"상품 {item.product_id} 없음")
        if product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"{product.product_name} 재고 부족 (남은 재고: {product.stock})")
        product.stock -= item.quantity
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    db.commit()
    return new_order


# ✅ 4️⃣ 특정 직원의 특정 날짜 주문 목록 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}", response_model=List[OrderSchema])
@router.get("/orders_archive/employee/{employee_id}/date/{order_date}", response_model=List[OrderSchema])
def get_orders_by_employee_date(
    employee_id: int,
    order_date: str,
    db: Session = Depends(get_db),
    is_archive: bool = Query(False)
):
    order_date_parsed = datetime.strptime(order_date, "%Y-%m-%d").date()
    year = order_date_parsed.year

    Order = OrderArchive if is_archive else get_order_model(year)

    orders = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date_parsed
    ).all()

    if not orders:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")
    return orders




@router.get("/employee/{employee_id}/date/{order_date}/items", response_model=List[dict])
def get_order_items_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    order_date_parsed = datetime.strptime(order_date, "%Y-%m-%d").date()
    year = order_date_parsed.year

    Order     = get_order_model(year)
    OrderItem = get_order_item_model(year)

    order = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date_parsed
    ).first()
    if not order:
        return JSONResponse(content=[], status_code=200, media_type="application/json; charset=utf-8")

    order_items = (
        db.query(
            OrderItem.product_id,
            OrderItem.quantity,
            Product.product_name,
            Product.category,
            Product.brand_id,
            Brand.name.label("brand_name")
        )
        .join(Product, Product.id == OrderItem.product_id)
        .join(Brand, Product.brand_id == Brand.id, isouter=True)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

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

    for category, brands in category_brand_dict.items():
        for brand_id, products in brands.items():
            brand_name = None
            for item in order_items:
                if item.brand_id == brand_id:
                    brand_name = item.brand_name
                    break
            formatted_result["items"].append({
                "category": category,
                "brand_id": brand_id,
                "brand_name": brand_name or "브랜드 없음",
                "products": products
            })

    return JSONResponse(content=formatted_result, media_type="application/json; charset=utf-8")



# ✅ 6️⃣ 특정 직원의 특정 날짜 주문 총합, 인센티브 합계, 총 박스 수량 조회
@router.get("/orders/employee/{employee_id}/date/{order_date}/summary", response_model=OrderSummarySchema)
def get_order_summary_by_employee_date(employee_id: int, order_date: str, db: Session = Depends(get_db)):
    order_date_parsed = datetime.strptime(order_date, "%Y-%m-%d").date()
    year = order_date_parsed.year

    Order = get_order_model(year)

    order = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date_parsed
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="해당 직원의 주문이 없습니다.")

    return {
        "total_amount": order.total_amount,
        "total_incentive": order.total_incentive,
        "total_boxes": order.total_boxes
    }



@router.get("/all_orders_by_shipment", response_model=List[dict])
def get_all_orders_by_shipment(date: str, shipment_round: int, db: Session = Depends(get_db)):
    order_date_parsed = datetime.strptime(date, "%Y-%m-%d").date()
    year = order_date_parsed.year

    Order     = get_order_model(year)
    OrderItem = get_order_item_model(year)

    orders = db.query(Order).filter(
        Order.order_date == order_date_parsed,
        Order.shipment_round == shipment_round
    ).all()

    if not orders:
        raise HTTPException(status_code=404, detail="해당 날짜 및 출고 차수에 주문이 없습니다.")

    aggregated_orders = {}

    for order in orders:
        order_items = (
            db.query(OrderItem, Product.product_name)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        for item in order_items:
            product_id = item.OrderItem.product_id
            quantity = item.OrderItem.quantity
            product_name = item.product_name

            if product_id in aggregated_orders:
                aggregated_orders[product_id]["quantity"] += quantity
            else:
                aggregated_orders[product_id] = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "quantity": quantity
                }

    return list(aggregated_orders.values())




@router.get("/orders_with_items", response_model=List[dict])
def get_orders_with_items(employee_id: int, date: str, shipment_round: int, db: Session = Depends(get_db)):
    order_date_parsed = datetime.strptime(date, "%Y-%m-%d").date()
    year = order_date_parsed.year

    Order     = get_order_model(year)
    OrderItem = get_order_item_model(year)

    orders = db.query(Order).filter(
        Order.employee_id == employee_id,
        Order.order_date == order_date_parsed,
        Order.shipment_round == shipment_round
    ).all()

    if not orders:
        raise HTTPException(status_code=404, detail="해당 직원의 해당 출고 차수에 대한 주문이 없습니다.")

    result = []
    for order in orders:
        order_items = (
            db.query(OrderItem, Product.product_name)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(OrderItem.order_id == order.id)
            .all()
        )

        items = [
            {
                "product_id": item.OrderItem.product_id,
                "product_name": item.product_name,
                "quantity": item.OrderItem.quantity
            }
            for item in order_items
        ]

        result.append({
            "order_id": order.id,
            "order_date": order.order_date,
            "shipment_round": order.shipment_round,
            "total_amount": order.total_amount,
            "total_boxes": order.total_boxes,
            "items": items
        })

    return result


# ✅ 기존 주문 덮어쓰기 (UPSERT)
@router.post("/orders/", response_model=OrderSchema)
def create_or_update_order(
    order_data: OrderCreateSchema,
    db: Session = Depends(get_db),
    is_archive: bool = Query(False)
):
    year = order_data.order_date.year
    Order     = OrderArchive if is_archive else get_order_model(year)
    OrderItem = OrderItemArchive if is_archive else get_order_item_model(year)

    # ✅ 기존 주문 조회
    existing_order = (
        db.query(Order)
        .filter(Order.employee_id == order_data.employee_id)
        .filter(Order.order_date == order_data.order_date)
        .first()
    )

    if existing_order:
        existing_order.total_amount = order_data.total_amount
        existing_order.total_incentive = order_data.total_incentive
        existing_order.total_boxes = order_data.total_boxes

        for item in order_data.order_items:
            existing_item = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == existing_order.id, OrderItem.product_id == item.product_id)
                .first()
            )
            if existing_item:
                existing_item.quantity = item.quantity
            else:
                db.add(OrderItem(order_id=existing_order.id, product_id=item.product_id, quantity=item.quantity))

        db.commit()
        db.refresh(existing_order)
        return existing_order

    # 신규 주문
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

    for item in order_data.order_items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    db.commit()
    return new_order




from fastapi import Body

@router.put("/update_quantity/{order_id}/")
def update_order_quantity(
    order_id: int,
    order_date: date,
    quantity: int = Body(..., embed=True),
    is_admin: bool = Query(False),
    db: Session = Depends(get_db)
):
    order_year = order_date.year
    OrderItem = get_order_item_model(order_year)

    lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    if lock and lock.is_locked and not is_admin:
        raise HTTPException(status_code=403, detail="이 날짜의 주문은 수정이 불가능합니다.")

    item = db.query(OrderItem).filter(OrderItem.id == order_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="해당 주문 항목을 찾을 수 없습니다.")

    item.quantity = quantity
    db.commit()
    return {"message": "주문 수량이 수정되었습니다.", "order_id": order_id, "quantity": quantity}

@router.get("/current_shipment_round/{order_date}")
def get_current_shipment_round(order_date: date, db: Session = Depends(get_db)):
    Order = get_order_model(order_date.year)

    round = (
        db.query(func.max(Order.shipment_round))
        .filter(Order.order_date == order_date)
        .scalar()
    ) or 0

    return {"shipment_round": round}


@router.get("/available_shipment_round/{order_date}")
def get_available_shipment_round(order_date: date, employee_id: int, db: Session = Depends(get_db)):
    from datetime import datetime, time

    Order = get_order_model(order_date.year)

    confirmed = (
        db.query(func.max(Order.shipment_round))
        .filter(Order.order_date == order_date, Order.is_confirmed == True)
        .scalar()
    ) or 0

    available = confirmed + 1

    existing = (
        db.query(Order)
        .filter(Order.employee_id == employee_id)
        .filter(Order.order_date == order_date)
        .filter(Order.shipment_round == available)
        .first()
    )

    now = datetime.now().time()
    if not existing:
        if not (now >= time(20, 0) or now <= time(7, 0)):
            raise HTTPException(status_code=403, detail="첫 주문은 20:00~07:00 사이에만 가능합니다.")

    return {"available_shipment_round": available}

# 예: app/routers/orders.py 내부
@router.get("/monthly_sales_product/{product_id}/{year}")
def get_monthly_sales_product(product_id: int, year: int, db: Session = Depends(get_db)):
    Order     = get_order_model(year)
    OrderItem = get_order_item_model(year)

    results = (
        db.query(
            extract("month", Order.order_date).label("sale_month"),
            func.sum(OrderItem.quantity).label("sum_qty")
        )
        .join(OrderItem, Order.id == OrderItem.order_id)
        .filter(OrderItem.product_id == product_id)
        .filter(extract("year", Order.order_date) == year)
        .group_by(extract("month", Order.order_date))
        .all()
    )

    monthly = [0] * 12
    for r in results:
        m = int(r.sale_month) - 1
        monthly[m] = int(r.sum_qty or 0)
    return monthly
