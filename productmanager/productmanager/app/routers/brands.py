# app/routers/brands.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.models.brands import Brand
from app.models.products import Product
from app.schemas.products import ProductOut
from app.schemas.brands import BrandCreate, BrandOut

router = APIRouter()

@router.post("/", response_model=BrandOut)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    """ 브랜드 추가 API """
    print("🔍 [DEBUG] 요청 받은 데이터:", payload.dict(), flush=True)  # ✅ 요청 데이터 확인
    existing = db.query(Brand).filter(Brand.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Brand already exists")

    new_brand = Brand(name=payload.name, description=payload.description)
    db.add(new_brand)
    db.commit()
    db.refresh(new_brand)
    return new_brand

@router.get("/", response_model=List[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    """ 브랜드 목록 조회 API """
    return db.query(Brand).all()

@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    """ 특정 브랜드 조회 API """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand

@router.delete("/{brand_id}")
def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    """ 브랜드 삭제 API """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    db.delete(brand)
    db.commit()
    return {"detail": "Brand deleted successfully"}