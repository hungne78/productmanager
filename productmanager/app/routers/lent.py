# app/routers/lent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.lent import Lent
from app.schemas.lent import LentCreate, LentOut

router = APIRouter()

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

@router.get("/lent", response_model=list[LentOut])
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
