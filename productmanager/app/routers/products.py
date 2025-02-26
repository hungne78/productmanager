# app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.products import Product
from app.schemas.products import ProductCreate, ProductOut
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional
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


from collections import defaultdict


@router.get("/all", response_model=list[ProductOut])
def list_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.get("/", response_model=dict)  # ✅ 상품 검색 및 필터링
def get_products(
    brand_id: Optional[int] = None,
    name: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if brand_id is not None:
        query = query.filter(Product.brand_id == brand_id)
    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))
    if barcode:
        query = query.filter(Product.barcode == barcode)

    products = query.all()
    if not products:
        return {}  # ✅ 빈 딕셔너리 반환

    categorized_products = defaultdict(list)
    for product in products:
        category = product.category or "미분류"
        categorized_products[category].append({
            "id": product.id,
            "product_name": product.product_name,
            "barcode": product.barcode,
            "default_price": product.default_price,
            "stock": product.stock,
            "is_active": product.is_active,
            "incentive": product.incentive,
            "box_quantity": product.box_quantity
        })
    return categorized_products


@router.put("/{product_id}", response_model=ProductOut)
def update_product_by_id(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
    """
    상품 ID를 기준으로 업데이트
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="해당 ID의 상품을 찾을 수 없습니다.")

    product.product_name = payload.product_name
    product.barcode = payload.barcode
    product.default_price = payload.default_price
    product.stock = payload.stock
    product.is_active = payload.is_active
    product.incentive = payload.incentive
    product.box_quantity = payload.box_quantity
    product.category = payload.category
    product.brand_id = payload.brand_id  # ✅ 브랜드 ID 유지

    db.commit()
    db.refresh(product)
    return product

@router.delete("/name/{product_name}")
def delete_product_by_name(product_name: str, db: Session = Depends(get_db)):
    """
    상품명을 기준으로 삭제
    """
    product = db.query(Product).filter(Product.product_name == product_name).first()
    if not product:
        raise HTTPException(status_code=404, detail="해당 상품명을 가진 상품을 찾을 수 없습니다.")
    
    db.delete(product)
    db.commit()
    return {"detail": f"상품 '{product_name}' 삭제 완료"}

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

@router.patch("/{product_id}/stock")
def update_product_stock(product_id: int, stock_increase: int, db: Session = Depends(get_db)):
    """
    상품 재고만 증가시키는 API
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock += stock_increase  # ✅ 기존 재고에 추가
    db.commit()
    db.refresh(product)
    return {"detail": f"Product ID {product_id} stock updated successfully. New stock: {product.stock}"}

# @router.get("/products", response_model=list[ProductOut])
# def list_products(db: Session = Depends(get_db)):
#     """
#     Return all products.
#     """
#     products = db.query(Product).all()
#     return products