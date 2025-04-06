# routers/category_price_override.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
import models, schemas

router = APIRouter(prefix="/category_price_overrides", tags=["카테고리 단가"])

@router.get("/", response_model=list[schemas.CategoryPriceOverrideOut])
def list_overrides(db: Session = Depends(get_db)):
    return db.query(models.CategoryPriceOverride).all()

@router.post("/", response_model=schemas.CategoryPriceOverrideOut)
def create_override(override: schemas.CategoryPriceOverrideCreate, db: Session = Depends(get_db)):
    db_override = models.CategoryPriceOverride(**override.dict())
    db.add(db_override)
    db.commit()
    db.refresh(db_override)
    return db_override

@router.put("/{override_id}", response_model=schemas.CategoryPriceOverrideOut)
def update_override(override_id: int, override: schemas.CategoryPriceOverrideUpdate, db: Session = Depends(get_db)):
    db_override = db.query(models.CategoryPriceOverride).filter_by(id=override_id).first()
    if not db_override:
        raise HTTPException(status_code=404, detail="Override not found")
    for key, value in override.dict().items():
        setattr(db_override, key, value)
    db.commit()
    return db_override

@router.delete("/{override_id}")
def delete_override(override_id: int, db: Session = Depends(get_db)):
    db_override = db.query(models.CategoryPriceOverride).filter_by(id=override_id).first()
    if not db_override:
        raise HTTPException(status_code=404, detail="Override not found")
    db.delete(db_override)
    db.commit()
    return {"ok": True}
