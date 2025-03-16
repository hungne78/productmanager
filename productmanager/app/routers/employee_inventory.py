from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_inventory import EmployeeInventory
from app.schemas.employee_inventory import InventoryUpdate
from app.models.products import Product
    
from app.models.employees import Employee  # ✅ 직원 목록 조회를 위해 import
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
