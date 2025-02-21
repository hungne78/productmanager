# app/routers/brands.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.db.database import get_db
from app.models.brands import Brand
from app.models.products import Product
from app.schemas.products import ProductOut

router = APIRouter()

@router.get("/{brand_id}/products", response_model=List[ProductOut])
def get_brand_products(brand_id: int, db: Session = Depends(get_db)):
    """
    한 브랜드에 속한 전체 상품 목록
    """
    brand = db.query(Brand).options(joinedload(Brand.products)).get(brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand.products
