from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_inventory import EmployeeInventory
from app.schemas.employee_inventory import InventoryUpdate

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

