from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.utils.push_service import send_push 
from app.models.clients import Client
router = APIRouter()

@router.post("/", response_model=FranchiseOrderOut)
def create_franchise_order(order_data: FranchiseOrderCreate, db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model, get_franchise_item_model

    year = order_data.order_date.year
    OrderModel = get_franchise_order_model(year)
    ItemModel = get_franchise_item_model(year)

    # ✅ 기존 주문 삭제
    existing = db.query(OrderModel).filter(
        OrderModel.client_id == order_data.client_id,
        OrderModel.order_date == order_data.order_date,
        OrderModel.shipment_round == order_data.shipment_round
    ).first()
    if existing:
        db.query(ItemModel).filter(ItemModel.order_id == existing.id).delete()
        db.delete(existing)
        db.commit()

    # ✅ 담당자 조회
    emp_id = db.query(EmployeeClient.employee_id).filter(
        EmployeeClient.client_id == order_data.client_id
    ).scalar()
    if not emp_id:
        raise HTTPException(status_code=404, detail="담당 영업사원을 찾을 수 없습니다.")

    # ✅ 주문 생성
    new_order = OrderModel(
        client_id=order_data.client_id,
        employee_id=emp_id,
        order_date=order_data.order_date,
        shipment_round=order_data.shipment_round
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order_data.items:
        db.add(ItemModel(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        ))
    db.commit()

    # ✅ 푸시 전송
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    client = db.query(Client).filter(Client.id == order_data.client_id).first()
    if not employee or not employee.fcm_token or not client:
        raise HTTPException(status_code=404, detail="푸시 발송 불가")

    send_push(
        fcm_token=employee.fcm_token,
        client_name=client.client_name,
        client_id=client.id,
        order_id=new_order.id
    )

    return {
        "id": new_order.id,
        "client_id": new_order.client_id,
        "client_name": client.client_name,
        "employee_id": new_order.employee_id,
        "order_date": new_order.order_date,
        "shipment_round": new_order.shipment_round,
        "is_transferred": new_order.is_transferred,
        "is_read": new_order.is_read,
        "created_at": new_order.created_at,
        "items": [
            {
                "product_id": i.product_id,
                "product_name": i.product.product_name if i.product else "알 수 없음",
                "quantity": i.quantity
            }
            for i in new_order.items
        ]
    }


@router.get("/by_employee/{employee_id}", response_model=List[FranchiseOrderOut])
def get_franchise_orders_by_employee(employee_id: int, year: int = Query(...), db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model

    OrderModel = get_franchise_order_model(year)
    orders = db.query(OrderModel).filter(
        OrderModel.employee_id == employee_id,
        OrderModel.is_transferred == False
    ).all()

    result = []
    for order in orders:
        client = db.query(Client).filter(Client.id == order.client_id).first()
        result.append({
            "id": order.id,
            "client_id": order.client_id,
            "client_name": client.client_name if client else "알 수 없음",
            "employee_id": order.employee_id,
            "order_date": order.order_date,
            "shipment_round": order.shipment_round,
            "is_transferred": order.is_transferred,
            "is_read": order.is_read,
            "created_at": order.created_at,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.product_name if item.product else "알 수 없음",
                    "quantity": item.quantity
                } for item in order.items
            ]
        })
    return result


@router.post("/orders/from_franchise/{franchise_order_id}")
def transfer_franchise_order(franchise_order_id: int, year: int = Query(...), db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model, get_franchise_item_model

    OrderModel = get_franchise_order_model(year)
    ItemModel = get_franchise_item_model(year)

    f_order = db.query(OrderModel).filter(OrderModel.id == franchise_order_id).first()
    if not f_order or f_order.is_transferred:
        raise HTTPException(status_code=400, detail="유효하지 않거나 이미 전송됨")

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

    items = db.query(ItemModel).filter(ItemModel.order_id == franchise_order_id).all()
    for item in items:
        db.add(OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity))

    f_order.is_transferred = True
    db.commit()

    return {"message": "주문 전송 완료", "order_id": new_order.id}


@router.get("/unread/{employee_id}", response_model=List[FranchiseOrderOut])
def get_unread_orders(employee_id: int, year: int = Query(...), db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model
    OrderModel = get_franchise_order_model(year)

    return db.query(OrderModel).filter(
        OrderModel.employee_id == employee_id,
        OrderModel.is_transferred == False,
        OrderModel.is_read == False
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

@router.patch("/{order_id}/mark_read")
def mark_order_as_read(order_id: int, year: int = Query(...), db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model
    OrderModel = get_franchise_order_model(year)

    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    order.is_read = True
    db.commit()
    return {"message": "읽음 처리 완료"}


@router.delete("/{order_id}")
def delete_franchise_order(order_id: int, year: int = Query(...), db: Session = Depends(get_db)):
    from app.utils.franchise_archive_utils import get_franchise_order_model, get_franchise_item_model
    OrderModel = get_franchise_order_model(year)
    ItemModel = get_franchise_item_model(year)

    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    db.query(ItemModel).filter(ItemModel.order_id == order.id).delete()
    db.delete(order)
    db.commit()
    return {"message": "주문 삭제 완료"}
