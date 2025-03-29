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
    특정 직원의 최신 차량 재고를 조회 (상품명 + 상품 분류 + 박스당 개수 + 상품 가격 포함)
    """
    inventory = (
        db.query(
            EmployeeInventory.product_id,
            EmployeeInventory.quantity,
            Product.product_name,
            Product.category,
            Product.box_quantity,  # ✅ 박스당 개수 추가
            Product.default_price  # ✅ 상품 가격 추가
        )
        .join(Product, EmployeeInventory.product_id == Product.id)
        .filter(EmployeeInventory.employee_id == employee_id)
        .all()
    )

    if not inventory:
        print(f"🚨 [경고] 직원 {employee_id}의 차량 재고가 없음.")
        return JSONResponse(content={"message": "해당 직원의 차량 재고가 없습니다.", "stock": []}, status_code=200)

    # ✅ JSON 변환 (상품명, 분류, 박스당 개수, 상품 가격, 재고 수량)
    stock_list = [
        {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "category": item.category if item.category else "미분류",
            "box_quantity": item.box_quantity,  # ✅ 박스당 개수
            "price": float(item.default_price),  # ✅ 상품 가격
            "quantity": item.quantity  # ✅ 재고 수량
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
    출고 확정 후 이번 차수 주문을 차량 재고에 반영 + 다음 차수 생성 (단, 아이템 복사는 안 함)
    """
    # ✅ 출고 확정 전에 마지막 차수에 주문이 있는지 먼저 확인
    

    # ✅ 1) 주문 잠금 체크
    order_lock = db.query(OrderLock).filter(OrderLock.lock_date == order_date).first()
    if not order_lock:
        raise HTTPException(status_code=404, detail="해당 날짜의 주문 잠금 기록이 없습니다.")
    if not order_lock.is_locked:
        raise HTTPException(status_code=403, detail="이 날짜가 잠겨있지 않습니다. 먼저 주문을 잠가주세요.")

    # ✅ 2) 현재 출고 차수 확인
    last_shipment_round = db.query(func.max(Order.shipment_round)) \
                            .filter(Order.order_date == order_date) \
                            .scalar() or 0
    
    order_count = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.order_date == order_date, Order.shipment_round == last_shipment_round)
        .count()
    )

    if order_count == 0:
        raise HTTPException(status_code=400, detail="주문이 없어서 출고차수가 변경되지 않았습니다.")


    current_shipment_round = last_shipment_round + 1
    print(f"🔔 [출고 확정] 이전 차수={last_shipment_round}, 새 차수={current_shipment_round}")

    # ✅ 3) 기존(이전 차수 포함) 출고된 내역 조회
    existing_shipments_query = (
        db.query(OrderItem.product_id, Order.employee_id, func.sum(OrderItem.quantity))
          .join(Order, OrderItem.order_id == Order.id)
          .filter(Order.order_date == order_date, Order.shipment_round < last_shipment_round)
          .group_by(OrderItem.product_id, Order.employee_id)
    )
    existing_shipments = {
        (emp_id, prod_id): total_qty
        for (prod_id, emp_id, total_qty) in existing_shipments_query.all()
    }

    # ✅ 이번(마지막) 차수의 주문 목록 조회 (차량 재고 반영용)
    last_orders_query = (
        db.query(OrderItem.product_id, Order.employee_id, func.sum(OrderItem.quantity))
          .join(Order, OrderItem.order_id == Order.id)
          .filter(Order.order_date == order_date, Order.shipment_round == last_shipment_round)
          .group_by(OrderItem.product_id, Order.employee_id)
    )
    last_orders = [
        {"employee_id": emp_id, "product_id": prod_id, "quantity": qty}
        for (prod_id, emp_id, qty) in last_orders_query.all()
    ]
    print(f"📌 [디버깅] 이번 차수({last_shipment_round}) 주문 데이터: {last_orders}")

    # ✅ 4) 차량 재고 업데이트
    for row in last_orders:
        emp_id = row["employee_id"]
        prod_id = row["product_id"]
        total_qty = row["quantity"]

        # 이미 출고된 수량
        already_shipped = existing_shipments.get((emp_id, prod_id), 0)
        quantity_to_ship = total_qty - already_shipped

        if quantity_to_ship <= 0:
            print(f"⚠️ 스킵: emp={emp_id}, product={prod_id} 이미 출고됨 or 없음")
            continue

        # ✅ 직원 차량 재고 추가
        inv_item = db.query(EmployeeInventory).filter(
            EmployeeInventory.employee_id == emp_id,
            EmployeeInventory.product_id == prod_id
        ).first()

        if inv_item:
            old_qty = inv_item.quantity
            inv_item.quantity += quantity_to_ship
            db.commit()
            print(f"🛒 [재고] emp={emp_id}, prod={prod_id}, 재고 {old_qty}→{inv_item.quantity}")
        else:
            new_inv = EmployeeInventory(
                employee_id=emp_id,
                product_id=prod_id,
                quantity=quantity_to_ship
            )
            db.add(new_inv)
            db.commit()
            print(f"➕ [재고추가] emp={emp_id}, prod={prod_id}, 수량={quantity_to_ship}")

    # ✅ 5) [중요] “새로운 차수 Order”를 아이템 없이 “빈”으로만 생성
    #     (원치 않으면 이 블록 전부 삭제 가능)
    #     아래 예시는 “이전 차수에 주문이 있었던 직원들”에게만 빈 Order를 만들어 준다.
    from collections import defaultdict
    employees_with_orders = set(row["employee_id"] for row in last_orders)

    for emp_id in employees_with_orders:
        # 혹은 회사 전체 직원이라면: for emp_id in db.query(Employee).all()...
        new_order_exists = db.query(Order.id).filter(
            Order.employee_id == emp_id,
            Order.order_date == order_date,
            Order.shipment_round == current_shipment_round
        ).first()

        if new_order_exists:
            # 이미 만들어져 있다면 스킵
            continue

        # “빈” 주문: 아이템은 복사하지 않음
        new_order = Order(
            employee_id=emp_id,
            order_date=order_date,
            shipment_round=current_shipment_round,
            total_amount=0,
            total_incentive=0,
            total_boxes=0
        )
        db.add(new_order)
        db.commit()
        print(f"🆕 [차수활성] emp={emp_id}, 차수={current_shipment_round} (빈 Order)")

    print(f"✅ [완료] 차량 재고 업데이트 (새 차수 복사 X)")

    # ✅ 6) 재고 업데이트
    if last_orders:
        emp_ids = set(o["employee_id"] for o in last_orders)
        for emp_id in emp_ids:
            update_vehicle_stock(emp_id, db, order_date)

    # ✅ 7) 잠금 해제
    order_lock.is_locked = False
    db.commit()
    db.refresh(order_lock)
    print(f"🔓 [잠금해제] date={order_date}, 출고확정→차수={current_shipment_round}")

    return {
        "message": f"{last_shipment_round}차 출고 확정 → {current_shipment_round}차 활성화(빈 주문만)",
        "updated_stock": last_orders
    }
