from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.category_price_override import CategoryPriceOverride
from app.schemas.category_price_override import (
    CategoryPriceOverrideCreate,
    CategoryPriceOverrideUpdate,
    CategoryPriceOverrideOut,
)
from typing import List 
from app.utils.time_utils import get_kst_now
router = APIRouter()

@router.get("/", response_model=List[CategoryPriceOverrideOut])
def list_overrides(db: Session = Depends(get_db)):
    """모든 카테고리 단가 오버라이드 조회"""
    return db.query(CategoryPriceOverride).all()

@router.post("/", response_model=CategoryPriceOverrideOut)
def create_override(override: CategoryPriceOverrideCreate, db: Session = Depends(get_db)):
    now_kst = get_kst_now().date()

    # 날짜가 누락된 경우 KST 기준 기본값으로 채우기 (선택사항)
    if not override.start_date:
        override.start_date = now_kst
    if not override.end_date:
        override.end_date = now_kst

    db_override = CategoryPriceOverride(**override.dict())
    db.add(db_override)
    db.commit()
    db.refresh(db_override)
    return db_override

@router.put("/{override_id}", response_model=CategoryPriceOverrideOut)
def update_override(override_id: int, override: CategoryPriceOverrideUpdate, db: Session = Depends(get_db)):
    """오버라이드 단가 수정"""
    db_override = db.query(CategoryPriceOverride).filter_by(id=override_id).first()
    if not db_override:
        raise HTTPException(status_code=404, detail="해당 오버라이드를 찾을 수 없습니다.")
    for key, value in override.dict(exclude_unset=True).items():
        setattr(db_override, key, value)
    db.commit()
    db.refresh(db_override)
    return db_override

@router.delete("/{override_id}")
def delete_override(override_id: int, db: Session = Depends(get_db)):
    """오버라이드 삭제"""
    db_override = db.query(CategoryPriceOverride).filter_by(id=override_id).first()
    if not db_override:
        raise HTTPException(status_code=404, detail="해당 오버라이드를 찾을 수 없습니다.")
    db.delete(db_override)
    db.commit()
    return {"ok": True}
