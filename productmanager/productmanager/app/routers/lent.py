# app/routers/lent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.lent import Lent
from app.schemas.lent import LentCreate, LentOut
from typing import List
router = APIRouter()

from pydantic import BaseModel
class RentRequest(BaseModel):
    freezer_id: int
    client_id: int

@router.post("/rent")
def rent_freezer(req: RentRequest, db: Session = Depends(get_db)):
    freezer = db.query(Lent).filter(Lent.id == req.freezer_id, Lent.client_id == 0).first()
    if not freezer:
        raise HTTPException(status_code=404, detail="이미 대여 중이거나 존재하지 않는 냉동고입니다.")
    
    freezer.client_id = req.client_id
    db.commit()
    return {"message": f"{freezer.serial_number} 대여 완료"}

@router.post("/lent", response_model=LentOut)
def create_lent(payload: LentCreate, db: Session = Depends(get_db)):
    # 필요 시, 클라이언트 존재 여부 등을 확인
    new_lent = Lent(
        client_id=payload.client_id,
        brand=payload.brand,
        serial_number=payload.serial_number,
        year=payload.year
    )
    db.add(new_lent)
    db.commit()
    db.refresh(new_lent)
    return new_lent
@router.get("/company", response_model=List[LentOut])
def get_company_freezers(db: Session = Depends(get_db)):
    """ 회사 보유 냉동고 (client_id == 0) 목록 조회 """
    return db.query(Lent).filter(Lent.client_id == 0).all()


@router.get("/lent", response_model=List[LentOut])
def list_lents(db: Session = Depends(get_db)):
    return db.query(Lent).all()

@router.get("/lent/{lent_id}", response_model=LentOut)
def get_lent(lent_id: int, db: Session = Depends(get_db)):
    lent = db.query(Lent).get(lent_id)
    if not lent:
        raise HTTPException(status_code=404, detail="Lent not found")
    return lent

@router.delete("/lent/{lent_id}")
def delete_lent(lent_id: int, db: Session = Depends(get_db)):
    lent = db.query(Lent).get(lent_id)
    if not lent:
        raise HTTPException(status_code=404, detail="Lent not found")
    db.delete(lent)
    db.commit()
    return {"detail": "Lent deleted"}

@router.get("/{client_id}", response_model=List[LentOut])  # ✅ 리스트로!
def get_lents_by_client(client_id: int, db: Session = Depends(get_db)):
    """ 거래처별 대여 냉동고 정보 전체 조회 """
    lents = db.query(Lent).filter(Lent.client_id == client_id).all()
    return lents

@router.post("/{client_id}", response_model=LentOut)
def create_lent(client_id: int, payload: LentCreate, db: Session = Depends(get_db)):
    """ 대여 냉동고 정보 등록 (여러 대 허용) """
    duplicate = db.query(Lent).filter(
        Lent.client_id == client_id,
        Lent.serial_number == payload.serial_number
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="이미 등록된 시리얼번호입니다.")

    lent = Lent(**payload.dict())
    db.add(lent)
    db.commit()
    db.refresh(lent)
    return lent


@router.put("/id/{lent_id}", response_model=LentOut)
def update_lent_by_id(lent_id: int, payload: LentCreate, db: Session = Depends(get_db)):
    lent = db.query(Lent).filter(Lent.id == lent_id).first()
    if not lent:
        raise HTTPException(status_code=404, detail="해당 냉동고 정보가 없습니다.")
    
    for key, value in payload.dict().items():
        setattr(lent, key, value)

    db.commit()
    db.refresh(lent)
    return lent


