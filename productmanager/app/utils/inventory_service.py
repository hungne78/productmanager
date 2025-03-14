from datetime import date
from sqlalchemy.orm import Session
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord
from app.models.orders import OrderItem, Order
from sqlalchemy import func  # Make sure this line is added at the top of your file
from app.models.products import Product  # ✅ Product 모델 import
def update_vehicle_stock(employee_id: int, db: Session):
    """
    특정 직원의 차량 재고를 주문 및 판매 데이터를 기반으로 자동 업데이트
    기존 주문 내역을 반영하여 중복 추가 방지
    """
    today = date.today()

    # ✅ 1. 현재 차량 재고 조회
    inventory = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
    stock_map = {item.product_id: item.quantity for item in inventory}

    # ✅ 2. 오늘 주문한 상품 가져오기 (기존 주문 반영)
    ordered_products = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.employee_id == employee_id, Order.order_date == today)
        .group_by(OrderItem.product_id)
        .all()
    )

    # ✅ 차량 재고에 주문 반영 (중복 추가 방지)
    for product_id, total_quantity in ordered_products:
        stock_map[product_id] = total_quantity  # ✅ 당일 주문한 총 수량으로 설정

    # ✅ 3. 오늘 판매한 상품 가져오기 (즉시 차감) - 박스 개수 고려
    sold_products = (
        db.query(SalesRecord.product_id, func.sum(SalesRecord.quantity), Product.box_quantity)
        .join(Product, SalesRecord.product_id == Product.id)  # 🔹 Product 테이블과 조인
        .filter(SalesRecord.employee_id == employee_id, SalesRecord.sale_datetime >= today)
        .group_by(SalesRecord.product_id, Product.box_quantity)
        .all()
    )

    for product_id, total_quantity, box_quantity in sold_products:
        # ✅ 박스 개수가 1보다 크면 (즉, 박스 단위로 판매되는 상품이면) 추가적인 곱셈이 필요한지 확인
        adjusted_quantity = total_quantity  # 기본적으로 받은 수량 사용

        print(f"🔍 상품 {product_id}: 박스당 {box_quantity}개, 판매된 수량 {total_quantity}")

        # ✅ 중복으로 곱하지 않도록 박스 개수 검토
        if total_quantity == box_quantity:
            print(f"⚠️ {product_id}는 박스당 개수({box_quantity})와 동일한 값이므로 추가 곱셈 생략")
        elif total_quantity % box_quantity == 0:
            print(f"⚠️ {product_id}는 개별 상품 기준으로 저장된 값이므로 추가 곱셈 필요")
            adjusted_quantity = total_quantity // box_quantity  # ✅ 박스 수량 기준으로 변환

        stock_map[product_id] = stock_map.get(product_id, 0) - adjusted_quantity  # ✅ 박스 고려하여 차감

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

