from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_inventory import EmployeeInventory
from app.schemas.employee_inventory import InventoryUpdate
from app.models.products import Product

router = APIRouter()

@router.get("/inventory/{employee_id}")
def get_employee_inventory(employee_id: int, db: Session = Depends(get_db)):
    """ 특정 직원 차량의 현재 재고 조회 """
    inventory = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
    if not inventory:
        return {"message": "해당 직원의 차량 재고가 없습니다."}
    return inventory

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

@router.get("/{employee_id}")
def get_vehicle_stock(employee_id: int, db: Session = Depends(get_db)):
    """
    특정 직원의 최신 차량 재고를 조회 (상품명 + 상품 분류 포함)
    """
    inventory = (
        db.query(EmployeeInventory.product_id, EmployeeInventory.quantity, Product.product_name, Product.category)  # ✅ 상품명 + 분류 추가
        .join(Product, EmployeeInventory.product_id == Product.id)
        .filter(EmployeeInventory.employee_id == employee_id)
        .all()
    )

    if not inventory:
        return {"message": "해당 직원의 차량 재고가 없습니다.", "stock": []}

    # ✅ JSON 변환 (상품 ID, 상품명, 상품 분류, 재고 수량)
    stock_list = [
        {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "category": item.category if item.category else "미분류",  # ✅ 카테고리가 없을 경우 "미분류" 표시
            "quantity": item.quantity
        }
        for item in inventory
    ]

    return {"stock": stock_list}
