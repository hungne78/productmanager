from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.franchise_order import FranchiseOrder, FranchiseOrderItem
from app.models.employee_clients import EmployeeClient
from app.models.orders import Order, OrderItem
from app.models.products import Product
from app.schemas.franchise_order import FranchiseOrderCreate, FranchiseOrderOut
from app.db.database import get_db
from typing import List
from app.models.employees import Employee
from pydantic import BaseModel

router = APIRouter()

@router.post("/", response_model=FranchiseOrderOut)
def create_franchise_order(order_data: FranchiseOrderCreate, db: Session = Depends(get_db)):
    existing = db.query(FranchiseOrder).filter(
        FranchiseOrder.client_id == order_data.client_id,
        FranchiseOrder.order_date == order_data.order_date,
        FranchiseOrder.shipment_round == order_data.shipment_round
    ).first()

    if existing:
        db.query(FranchiseOrderItem).filter(FranchiseOrderItem.order_id == existing.id).delete()
        db.delete(existing)
        db.commit()

    emp_id = db.query(EmployeeClient.employee_id).filter(
        EmployeeClient.client_id == order_data.client_id
    ).scalar()

    if not emp_id:
        raise HTTPException(status_code=404, detail="담당 영업사원을 찾을 수 없습니다.")

    new_order = FranchiseOrder(
        client_id=order_data.client_id,
        employee_id=emp_id,
        order_date=order_data.order_date,
        shipment_round=order_data.shipment_round
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order_data.items:
        db.add(FranchiseOrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        ))
    db.commit()
    return new_order


@router.get("/franchise_orders/by_employee/{employee_id}", response_model=List[FranchiseOrderOut])
def get_franchise_orders_by_employee(employee_id: int, db: Session = Depends(get_db)):
    return db.query(FranchiseOrder).filter(
        FranchiseOrder.employee_id == employee_id,
        FranchiseOrder.is_transferred == False
    ).all()


@router.post("/orders/from_franchise/{franchise_order_id}")
def transfer_franchise_order(franchise_order_id: int, db: Session = Depends(get_db)):
    f_order = db.query(FranchiseOrder).filter(FranchiseOrder.id == franchise_order_id).first()
    if not f_order or f_order.is_transferred:
        raise HTTPException(status_code=400, detail="유효하지 않거나 이미 전송된 주문입니다.")

    new_order = Order(
        employee_id=f_order.employee_id,
        order_date=f_order.order_date,
        shipment_round=f_order.shipment_round,
        total_amount=0,
        total_incentive=0,
        total_boxes=0
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    items = db.query(FranchiseOrderItem).filter(FranchiseOrderItem.order_id == franchise_order_id).all()
    for item in items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    f_order.is_transferred = True
    db.commit()

    return {"message": "주문 전송 완료", "order_id": new_order.id}

@router.get("/unread/{employee_id}", response_model=List[FranchiseOrderOut])
def get_unread_orders(employee_id: int, db: Session = Depends(get_db)):
    return db.query(FranchiseOrder).filter(
        FranchiseOrder.employee_id == employee_id,
        FranchiseOrder.is_transferred == False,
        FranchiseOrder.is_read == False
    ).all()



class FCMTokenIn(BaseModel):
    token: str

@router.post("/fcm_token/{employee_id}")
def save_fcm_token(employee_id: int, token_data: FCMTokenIn, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="직원 정보가 없습니다.")

    employee.fcm_token = token_data.token
    db.commit()
    return {"message": "FCM 토큰 저장 완료"}