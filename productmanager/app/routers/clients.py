from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientOut
from fastapi.responses import JSONResponse
from app.models.employee_clients import EmployeeClient
from app.utils.time_utils import convert_utc_to_kst
from starlette.responses import JSONResponse, StreamingResponse
import json

router = APIRouter()

@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """ 새로운 거래처 등록 (KST로 저장) """
    new_client = Client(
        client_name=payload.client_name,
        address=payload.address,
        phone=payload.phone,
        outstanding_amount=payload.outstanding_amount,
        regular_price=payload.regular_price,
        fixed_price=payload.fixed_price,
        business_number=payload.business_number,
        email=payload.email
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client  # ✅ 변환 없이 그대로 반환

@router.get("/clients", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """ 모든 거래처 목록 조회 (KST 그대로 반환) """
    clients = db.query(Client).all()
    return clients  # ✅ 변환 없이 그대로 반환


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """ 특정 거래처 조회 (KST 변환 없음) """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client  # ✅ 변환 없이 그대로 반환


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientCreate, db: Session = Depends(get_db)):
    """ 거래처 정보 수정 """
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_client.client_name = payload.client_name
    db_client.address = payload.address
    db_client.phone = payload.phone
    db_client.outstanding_amount = payload.outstanding_amount
    db_client.regular_price = payload.regular_price
    db_client.fixed_price = payload.fixed_price
    db_client.business_number = payload.business_number
    db_client.email = payload.email

    db.commit()
    db.refresh(db_client)
    return db_client  # ✅ 변환 없이 그대로 반환

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """ 특정 거래처 삭제 (연결된 직원-거래처 정보 먼저 삭제) """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다.")

    try:
        # ✅ 연결된 직원-거래처 관계 삭제
        db.query(EmployeeClient).filter(EmployeeClient.client_id == client_id).delete()

        # ✅ 거래처 삭제
        db.delete(client)
        db.commit()

        return {"message": "거래처가 삭제되었습니다."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"거래처 삭제 실패: {str(e)}")

@router.put("/{client_id}/outstanding")
def update_outstanding(client_id: int, payload: dict, db: Session = Depends(get_db)):
    """ 거래처 미수금(outstanding_amount) 업데이트 """
    db_client = db.query(Client).filter(Client.id == client_id).first()

    if not db_client:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다.")

    if "outstanding_amount" not in payload:
        raise HTTPException(status_code=400, detail="outstanding_amount 필드가 필요합니다.")

    try:
        db_client.outstanding_amount = payload["outstanding_amount"]
        db.commit()
        db.refresh(db_client)

        return {"message": "미수금이 업데이트되었습니다.", "outstanding_amount": db_client.outstanding_amount}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"미수금 업데이트 실패: {str(e)}")
