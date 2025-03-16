from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord

# ✅ KST(한국 시간, UTC+9)로 변환하는 함수
def get_kst_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))

def update_vehicle_stock(employee_id: int, db: Session):
    """
    특정 직원의 차량 재고를 즉시 업데이트 (판매 반영, 주문은 반영하지 않음)
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
    return {"message": "판매 반영 완료", "updated_stock": stock_map}
