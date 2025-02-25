# app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.products import Product
from app.schemas.products import ProductCreate, ProductOut
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
router = APIRouter()

@router.post("/", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(
        brand_id=payload.brand_id,
        product_name=payload.product_name,
        barcode=payload.barcode,
        default_price=payload.default_price,
        stock=payload.stock,
        is_active=payload.is_active,
        incentive=payload.incentive,
        box_quantity=payload.box_quantity,  # ✅ 박스당 개수 추가
        category=payload.category  # ✅ 상품 분류 추가
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    """
    상품 정보 업데이트
    """
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    product.brand_id = payload.brand_id
    product.product_name = payload.product_name
    product.barcode = payload.barcode
    product.default_price = payload.default_price
    product.stock = payload.stock
    product.is_active = payload.is_active
    product.incentive = payload.incentive
    product.box_quantity = payload.box_quantity  # ✅ 박스당 개수 업데이트
    product.category = payload.category  # ✅ 상품 분류 업데이트

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}

@router.get("/barcode/{barcode}", response_model=ProductOut)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    바코드로 상품 조회 (UTF-8 인코딩 문제 해결)
    """
    product = db.query(Product).filter(Product.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found with this barcode")

    product_dict = jsonable_encoder(product)

    # JSONResponse에 넣을 때 utf-8 명시
    return JSONResponse(content=product_dict, media_type="application/json; charset=utf-8")
