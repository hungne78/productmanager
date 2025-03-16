from datetime import date
from sqlalchemy.orm import Session
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord
from app.models.orders import OrderItem, Order
from sqlalchemy import func  # Make sure this line is added at the top of your file
from app.models.products import Product  # ✅ Product 모델 import
from datetime import datetime

def update_vehicle_stock(employee_id: int, db: Session):
    """
    특정 직원의 차량 재고를 주문 및 판매 데이터를 기반으로 자동 업데이트
    """
    today = date.today()

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
        last_update_time = datetime(today.year, today.month, today.day)  # 기본값 설정

    print(f"🕒 [디버깅] 최근 재고 업데이트 시각: {last_update_time}")

    # ✅ 기존 주문 조회
    previous_orders = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.employee_id == employee_id, Order.order_date == today)
        .group_by(OrderItem.product_id)
        .all()
    )
    previous_order_map = {product_id: total_quantity for product_id, total_quantity in previous_orders}

    # ✅ 새로운 주문 조회
    new_orders = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.employee_id == employee_id, Order.order_date == today)
        .group_by(OrderItem.product_id)
        .all()
    )
    new_order_map = {product_id: total_quantity for product_id, total_quantity in new_orders}

    # ✅ 차량 재고 업데이트 (주문 반영 - 증가)
    for product_id, new_quantity in new_order_map.items():
        previous_quantity = previous_order_map.get(product_id, 0)
        difference = new_quantity - previous_quantity  # ✅ 주문량 변화 반영

        print(f"📌 [주문 반영] 상품 {product_id}: 기존 주문 {previous_quantity}박스 → 수정 후 {new_quantity}박스 (변화량: +{difference})")

        stock_map[product_id] = stock_map.get(product_id, 0) + difference  # ✅ 차량 재고 증가!

    # ✅ 오늘 판매한 상품 차감 (과거 판매 내역 중복 차감 방지)
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

    # ✅ 차량 재고 업데이트 (DB 반영)
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
    return {"message": "차량 재고 자동 업데이트 완료", "updated_stock": stock_map}
