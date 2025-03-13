from datetime import date
from sqlalchemy.orm import Session
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord
from app.models.orders import OrderItem, Order

def update_vehicle_stock(employee_id: int, db: Session):
    """
    특정 직원의 차량 재고를 주문 및 판매 데이터를 기반으로 자동 업데이트
    """
    today = date.today()

    # ✅ 1. 현재 차량 재고 조회
    inventory = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
    stock_map = {item.product_id: item.quantity for item in inventory}

    # ✅ 2. 오늘 주문한 상품 가져오기 (1번만 추가)
    ordered_products = (
        db.query(OrderItem.product_id, OrderItem.quantity)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.employee_id == employee_id, Order.order_date == today)
        .all()
    )

    processed_products = set()  # ✅ 주문 중복 방지
    for product_id, quantity in ordered_products:
        if product_id not in processed_products:
            stock_map[product_id] = stock_map.get(product_id, 0) + quantity
            processed_products.add(product_id)

    # ✅ 3. 오늘 판매한 상품 가져오기 (즉시 차감)
    sold_products = (
        db.query(SalesRecord.product_id, SalesRecord.quantity)
        .filter(SalesRecord.employee_id == employee_id, SalesRecord.sale_datetime >= today)
        .all()
    )

    for product_id, quantity in sold_products:
        stock_map[product_id] = stock_map.get(product_id, 0) - quantity

    # ✅ 4. 차량 재고 업데이트 (기존 데이터 수정)
    for product_id, quantity in stock_map.items():
        inventory_item = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == employee_id,
            EmployeeInventory.product_id == product_id
        ).first()

        if inventory_item:
            inventory_item.quantity = quantity  # ✅ 기존 데이터 업데이트
        else:
            new_item = EmployeeInventory(employee_id=employee_id, product_id=product_id, quantity=quantity)
            db.add(new_item)  # ✅ 새 데이터 추가

    db.commit()
    return {"message": "차량 재고 자동 업데이트 완료", "updated_stock": stock_map}
