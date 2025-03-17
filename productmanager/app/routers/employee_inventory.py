from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from sqlalchemy import func
from app.models.employee_inventory import EmployeeInventory
from app.schemas.employee_inventory import InventoryUpdate
from app.models.products import Product
from datetime import date    
from app.models.orders import OrderLock
from app.models.employees import Employee  # ✅ 직원 목록 조회를 위해 import
from app.models.orders import Order, OrderItem
from app.utils.inventory_service import update_vehicle_stock
router = APIRouter()

# @router.get("/inventory/{employee_id}")
# def get_employee_inventory(employee_id: int, db: Session = Depends(get_db)):
#     """ 특정 직원 차량의 현재 재고 조회 """
#     inventory = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
#     if not inventory:
#         return {"message": "해당 직원의 차량 재고가 없습니다."}
#     return inventory

@router.put("/inventory/update")
def update_employee_inventory(payload: InventoryUpdate, db: Session = Depends(get_db)):
    """ 직원 차량 재고 업데이트 (신규 제품 자동 추가) """
    for item in payload.items:
        inventory_record = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == payload.employee_id,
            EmployeeInventory.product_id == item.product_id
        ).first()

        if inventory_record:
            inventory_record.quantity = item.quantity  # ✅ 기존 재고 업데이트
        else:
            # ✅ 새로운 제품이면 추가
            new_inventory = EmployeeInventory(
                employee_id=payload.employee_id,
                product_id=item.product_id,
                quantity=item.quantity
            )
            db.add(new_inventory)

    db.commit()
    return {"message": "차량 재고 업데이트 완료"}

from fastapi.responses import JSONResponse
import json

@router.get("/{employee_id}")
def get_vehicle_stock(employee_id: int, db: Session = Depends(get_db)):
    """
    특정 직원의 최신 차량 재고를 조회 (상품명 + 상품 분류 포함)
    """
    inventory = (
        db.query(EmployeeInventory.product_id, EmployeeInventory.quantity, Product.product_name, Product.category)
        .join(Product, EmployeeInventory.product_id == Product.id)
        .filter(EmployeeInventory.employee_id == employee_id)
        .all()
    )

    if not inventory:
        print(f"🚨 [경고] 직원 {employee_id}의 차량 재고가 없음.")
        return JSONResponse(content={"message": "해당 직원의 차량 재고가 없습니다.", "stock": []}, status_code=200)

    # ✅ JSON 변환 (상품 ID, 상품명, 상품 분류, 재고 수량)
    stock_list = [
        {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "category": item.category if item.category else "미분류",
            "quantity": item.quantity
        }
        for item in inventory
    ]

    print(f"📡 [응답 데이터] 직원 {employee_id} 차량 재고: {json.dumps(stock_list, ensure_ascii=False)}")    

    return JSONResponse(content={"stock": stock_list}, status_code=200, media_type="application/json")

    

from app.models.employee_inventory import EmployeeInventory
from app.models.employees import Employee  # ✅ 직원 목록 조회를 위해 import



@router.post("/add_product/{product_id}")
def add_product_to_all_employee_inventory(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    모든 직원의 차량 재고에 새로운 상품 추가
    """
    # ✅ 1. 서버에 존재하는 모든 직원 ID 조회
    all_employee_ids = db.query(Employee.id).all()  # 모든 직원 ID 가져오기

    if not all_employee_ids:
        raise HTTPException(status_code=404, detail="등록된 직원이 없습니다.")

    added_count = 0  # ✅ 성공적으로 추가된 직원 수 추적

    for (employee_id,) in all_employee_ids:  # employee_id 튜플에서 값 추출
        # ✅ 2. 직원 차량 재고에 이미 존재하는지 확인
        inventory_record = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == employee_id,
            EmployeeInventory.product_id == product_id
        ).first()

        if inventory_record:
            print(f"🚨 직원 {employee_id}의 차량 재고에 이미 상품 {product_id} 존재.")
            continue  # 이미 존재하면 추가하지 않음

        # ✅ 3. 새로운 제품이면 추가
        new_inventory = EmployeeInventory(
            employee_id=employee_id,
            product_id=product_id,
            quantity=0  # 초기 수량은 0으로 설정
        )
        db.add(new_inventory)
        added_count += 1

    db.commit()

    return {"message": f"상품 {product_id}가 {added_count}명의 직원 차량 재고에 추가되었습니다."}

@router.post("/finalize_inventory/{order_date}")
def finalize_inventory(order_date: date, db: Session = Depends(get_db)):
    """
    출고 확정 후 주문 데이터를 차량 재고에 반영 (다단계 출고 지원)
    """
    # ✅ 주문이 잠겨 있는지 확인
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    if not order_lock:
        raise HTTPException(status_code=404, detail="해당 날짜의 주문 잠금 기록이 없습니다.")

    if not order_lock.is_locked:
        raise HTTPException(status_code=403, detail="이 날짜의 주문이 아직 잠겨있지 않습니다. 먼저 주문을 잠가주세요.")

    # ✅ 현재 출고 단계 확인 (1차, 2차, 3차 출고 등)
    last_shipment_round = db.query(func.max(Order.shipment_round)).filter(
        Order.order_date == order_date
    ).scalar() or 0
    current_shipment_round = last_shipment_round + 1  # ✅ 이번 출고는 이전 출고 +1

    # ✅ 기존 출고된 내역 가져오기 (이미 출고된 수량 방지)
    existing_shipments_query = (
        db.query(OrderItem.product_id, Order.employee_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.order_date == order_date, Order.shipment_round < current_shipment_round)
        .group_by(OrderItem.product_id, Order.employee_id)
    )
    existing_shipments = {
        (employee_id, product_id): total_quantity
        for product_id, employee_id, total_quantity in existing_shipments_query.all()
    }

    # ✅ 현재 출고할 주문 내역 가져오기 (출고 차수별로 새로운 주문 기록 필요)
    last_orders_query = (
        db.query(OrderItem.product_id, Order.employee_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.order_date == order_date, Order.shipment_round == last_shipment_round)
        .group_by(OrderItem.product_id, Order.employee_id)
    )

    last_orders = [
        {"employee_id": employee_id, "product_id": product_id, "quantity": total_quantity}
        for product_id, employee_id, total_quantity in last_orders_query.all()
    ]

    print(f"📌 [디버깅] 최종 주문 데이터: {last_orders}")

    # ✅ 차량 재고 업데이트 (이번 출고분만 반영)
    for order in last_orders:
        employee_id = order["employee_id"]
        product_id = order["product_id"]
        total_quantity = order["quantity"]

        # ✅ 기존 출고 내역 확인
        already_shipped = existing_shipments.get((employee_id, product_id), 0)
        quantity_to_ship = total_quantity - already_shipped  # ✅ 새로 출고해야 할 수량

        if quantity_to_ship <= 0:
            print(f"⚠️ [스킵] 직원 {employee_id} - 제품 {product_id} 이미 전량 출고됨 (추가 출고 없음)")
            continue  # ✅ 이미 출고된 경우 추가 출고 방지

        print(f"🔄 [출고 반영] 직원 {employee_id} - 제품 {product_id} 기존 출고 {already_shipped}, 이번 출고 {quantity_to_ship}")

        # ✅ 차량 재고 업데이트
        inventory_item = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == employee_id,
            EmployeeInventory.product_id == product_id
        ).first()

        if inventory_item:
            print(f"🛒 [재고 업데이트] 직원 {employee_id} - 제품 {product_id} 차량 재고 {inventory_item.quantity} → {inventory_item.quantity + quantity_to_ship}")
            inventory_item.quantity += quantity_to_ship
            db.commit()  # ✅ 강제 반영
            db.refresh(inventory_item)  # ✅ 최신 데이터 반영
        else:
            print(f"➕ [새 제품 추가] 직원 {employee_id} - 제품 {product_id}, 초기 재고 {quantity_to_ship}")
            new_item = EmployeeInventory(
                employee_id=employee_id,
                product_id=product_id,
                quantity=quantity_to_ship
            )
            db.add(new_item)
            db.commit()  # ✅ 강제 반영
            db.refresh(new_item)  # ✅ 최신 데이터 반영

    # ✅ 새로운 주문 생성 (출고 차수 업데이트)
    for order in last_orders:
        new_order = Order(
            employee_id=order["employee_id"],
            order_date=order_date,
            total_amount=0,  # ✅ 출고 확정 시 금액 정보 불필요
            total_incentive=0,
            total_boxes=0,
            shipment_round=current_shipment_round  # ✅ 출고 차수 업데이트
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)

        # ✅ 새 주문 항목 추가
        new_order_item = OrderItem(
            order_id=new_order.id,
            product_id=order["product_id"],
            quantity=order["quantity"]
        )
        db.add(new_order_item)
        db.commit()

    print(f"✅ [완료] 차량 재고 자동 업데이트 완료")

    # ✅ 🚀 출고 반영 후 차량 재고 업데이트 실행 (중복 방지)
    print(f"[차량 재고 업데이트 실행] 직원 {employee_id}")
    update_vehicle_stock(employee_id, db, order_date)  # ✅ order_date 추가하여 호출

    # ✅ 출고 확정 후, 주문을 다시 개방하여 추가 주문 가능하게 설정
    order_lock.is_locked = False  # ✅ 주문 다시 개방
    db.commit()
    db.refresh(order_lock)

    return {
        "message": f"출고 확정 완료 (출고 단계: {current_shipment_round})",
        "updated_stock": last_orders
    }

