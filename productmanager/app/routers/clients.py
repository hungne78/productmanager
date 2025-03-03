from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientOut
from fastapi.responses import JSONResponse
from app.models.employee_clients import EmployeeClient

import json

router = APIRouter()

@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """
    새로운 거래처 등록
    """
    new_client = Client(
        client_name=payload.client_name,
        address=payload.address,
        phone=payload.phone,
        outstanding_amount=payload.outstanding_amount,
        regular_price=payload.regular_price,  # ✅ 일반가
        fixed_price=payload.fixed_price,      # ✅ 고정가  # 거래처 단가 추가
        business_number=payload.business_number,  # 사업자번호 추가
        email=payload.email  # 메일주소 추가
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client

def convert_datetime(obj):
    """
    datetime 타입을 JSON 직렬화할 수 있도록 변환
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

@router.get("/", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """
    거래처 목록 조회
    """
    clients = db.query(Client).all()
    # Pydantic V2에서는 from_orm 대신 model_validate 사용
    result = [ClientOut.model_validate(client).model_dump() for client in clients]
    return JSONResponse(
        content=json.loads(json.dumps(result, default=convert_datetime)),
        media_type="application/json; charset=utf-8"
    )

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """
    특정 거래처 조회
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientCreate, db: Session = Depends(get_db)):
    """
    거래처 정보 수정
    """
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_client.client_name = payload.client_name
    db_client.address = payload.address
    db_client.phone = payload.phone
    db_client.outstanding_amount = payload.outstanding_amount  # 미수금 업데이트 추가
    db_client.regular_price = payload.regular_price  # 거래처 단가 업데이트
    db_client.fixed_price = payload.fixed_price 
    db_client.business_number = payload.business_number  # 사업자번호 업데이트
    db_client.email = payload.email  # 메일주소 업데이트

    db.commit()
    db.refresh(db_client)
    return db_client

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

