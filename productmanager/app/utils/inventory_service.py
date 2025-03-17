from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord
from app.models.orders import Order, OrderItem  
# ✅ KST(한국 시간, UTC+9)로 변환하는 함수
def get_kst_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

def update_vehicle_stock(employee_id: int, db: Session, order_date: date):
    """
    특정 직원의 차량 재고를 즉시 업데이트 (판매 반영 + 출고 확정 반영)
    """
    # ✅ 현재 차량 재고 조회
    inventory = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
    stock_map = {item.product_id: item.quantity for item in inventory}

    # ✅ 최근 업데이트 시간 조회
    last_update_time = (
        db.query(func.max(EmployeeInventory.updated_at))
        .filter(EmployeeInventory.employee_id == employee_id)
        .scalar()
    )
    if last_update_time is None:
        last_update_time = datetime.combine(order_date, datetime.min.time())  # 기본값 설정

    print(f"🕒 [디버깅] 최근 재고 업데이트 시각: {last_update_time}")

    # ✅ 🚀 가장 최근 출고 차수 조회
    last_shipment_round = (
        db.query(func.max(Order.shipment_round))
        .filter(Order.employee_id == employee_id, Order.order_date == order_date)
        .scalar()
    ) or 0

    print(f"📌 [디버깅] {order_date} 직원 {employee_id} 마지막 출고 차수: {last_shipment_round}")

    # ✅ 🚛 가장 최근 출고 차수의 주문만 반영 (중복 추가 방지)
    shipped_orders = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.employee_id == employee_id,
            Order.order_date == order_date,
            Order.shipment_round == last_shipment_round  # ✅ 가장 최근 출고 차수만 반영
        )
        .group_by(OrderItem.product_id)
        .all()
    )

    for product_id, total_quantity in shipped_orders:
        print(f"🚛 [출고 반영] 상품 {product_id}: 출고된 수량 {total_quantity}박스 추가")
        stock_map[product_id] = stock_map.get(product_id, 0) + total_quantity  # ✅ 출고 확정 시 차량 재고 증가

    # ✅ 🔻 오늘 판매한 상품 차감 (중복 차감 방지)
    sold_products = (
        db.query(SalesRecord.product_id, func.sum(SalesRecord.quantity))
        .filter(
            SalesRecord.employee_id == employee_id,
            SalesRecord.sale_datetime > last_update_time  # ✅ 가장 최근 업데이트 이후의 판매 기록만 반영
        )
        .group_by(SalesRecord.product_id)
        .all()
    )

    for product_id, total_quantity in sold_products:
        print(f"🔍 [판매 반영] 상품 {product_id}: 최근 판매된 수량 {total_quantity}박스")
        stock_map[product_id] = stock_map.get(product_id, 0) - total_quantity  # ✅ 판매 시 재고 감소!

    # ✅ 🚀 차량 재고 업데이트 (DB 반영)
    for product_id, quantity in stock_map.items():
        inventory_item = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == employee_id,
            EmployeeInventory.product_id == product_id
        ).first()

        if inventory_item:
            print(f"🔄 [업데이트] 제품 {product_id} 차량 재고 {inventory_item.quantity} → {quantity}")
            inventory_item.quantity = quantity  # ✅ 기존 데이터 업데이트
            inventory_item.updated_at = datetime.now()  # ✅ 최신 업데이트 시간 기록
        else:
            print(f"➕ [새 제품 추가] 제품 {product_id}, 초기 재고 {quantity}")
            new_item = EmployeeInventory(
                employee_id=employee_id,
                product_id=product_id,
                quantity=quantity,
                updated_at=datetime.now()
            )
            db.add(new_item)  # ✅ 새 데이터 추가

    db.commit()
    print(f"✅ [완료] 차량 재고 자동 업데이트 완료")
    return {"message": "출고 및 판매 반영 완료", "updated_stock": stock_map}
