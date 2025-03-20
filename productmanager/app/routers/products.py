# app/routers/products.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.products import Product
from app.schemas.products import ProductCreate, ProductOut, ProductResponse, ProductUpdate
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.utils.time_utils import get_kst_now, convert_utc_to_kst 
router = APIRouter()

class StockUpdateRequest(BaseModel):
    stock_change: int

class ReserveRequest(BaseModel):
    quantity: int

class CancelReservationRequest(BaseModel):
    quantity: int

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
        box_quantity=payload.box_quantity,
        category=payload.category,
        is_fixed_price=payload.is_fixed_price
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return convert_product_to_kst(new_product)  # ✅ KST 변환 후 반환


from collections import defaultdict

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductCreate, db: Session = Depends(get_db)):
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
    product.box_quantity = payload.box_quantity
    product.category = payload.category
    product.is_fixed_price = payload.is_fixed_price
    product.updated_at = get_kst_now()  # ✅ KST 적용

    db.commit()
    db.refresh(product)
    return convert_product_to_kst(product)  # ✅ KST 변환 후 반환


@router.get("/", response_model=dict)
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
            "brand_id": product.brand_id,
            "product_name": product.product_name,
            "barcode": product.barcode,
            "default_price": product.default_price,
            "stock": product.stock,
            "is_active": product.is_active,
            "incentive": product.incentive,
            "box_quantity": product.box_quantity,
            "is_fixed_price": product.is_fixed_price  # ✅ 가격 유형 추가
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
    product.is_fixed_price = payload.is_fixed_price 
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

@router.get("/warehouse_stock", response_model=List[dict])
def get_warehouse_stock(db: Session = Depends(get_db)):
    """
    창고 재고 목록을 반환하는 API
    """
    try:
        products = db.query(Product.id, Product.product_name, Product.stock).all()

        return [
            {"product_id": p.id, "product_name": p.product_name, "quantity": p.stock} for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 창고 재고 조회 실패: {str(e)}")
    
@router.put("/{product_id}/reserve")
def reserve_product_stock(product_id: int, request: ReserveRequest, db: Session = Depends(get_db)):
    """ 🔥 사용자가 + 버튼을 눌렀을 때, 창고 재고에서 예약 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock_reserved += request.quantity  # ✅ 예약된 재고 증가
        product.stock -= request.quantity  # ✅ 실재고 차감
        db.commit()

    return {"message": "✅ 예약 성공", "new_stock": product.stock, "reserved_stock": product.stock_reserved}

# @router.get("/products", response_model=list[ProductOut])
# def list_products(db: Session = Depends(get_db)):
#     """
#     Return all products.
#     """
#     products = db.query(Product).all()
#     return products
@router.get("/all", response_model=list[ProductOut])
def list_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [convert_product_to_kst(product) for product in products]  # ✅ KST 변환 적용

@router.put("/{product_id}/reserve")
def reserve_product_stock(product_id: int, quantity: int, db: Session = Depends(get_db)):
    """ 🔥 사용자가 + 버튼을 눌렀을 때, 창고 재고에서 예약 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock < quantity:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock_reserved += quantity  # ✅ 예약된 재고 증가
        product.stock -= quantity  # ✅ 실재고 차감
        db.commit()

    return {"message": "✅ 예약 성공", "new_stock": product.stock, "reserved_stock": product.stock_reserved}

@router.put("/{product_id}/cancel_reservation")
def cancel_product_reservation(product_id: int, request: CancelReservationRequest, db: Session = Depends(get_db)):
    """ 🔥 사용자가 - 버튼을 눌렀거나, 주문을 취소할 때 예약 해제 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock_reserved < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 예약된 재고 부족!")

        product.stock_reserved -= request.quantity  # ✅ 예약된 재고 감소
        product.stock += request.quantity  # ✅ 실재고 복구
        db.commit()

    return {"message": "✅ 예약 취소 성공", "new_stock": product.stock, "reserved_stock": product.stock_reserved}


@router.get("/stock")
def get_warehouse_stock(db: Session = Depends(get_db)):
    """ 🔥 모든 제품의 최신 창고 재고 가져오기 """
    products = db.query(Product).all()
    return [{"id": product.id, "stock": product.stock} for product in products]


@router.put("/{product_id}/stock")
def update_product_stock(product_id: int, request: StockUpdateRequest, db: Session = Depends(get_db)):
    with db.begin():  # ✅ 트랜잭션 시작
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock + request.stock_change < 0:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock += request.stock_change  # ✅ 재고 차감 또는 복구
        db.commit()  # ✅ 트랜잭션 완료

    return {"message": "✅ 재고 업데이트 성공", "new_stock": product.stock}

@router.get("/", response_model=dict)
def fetch_products(search: str = Query(None), db: Session = Depends(get_db)):
    """
    상품 목록 조회 (이름 검색 포함)
    """
    query = db.query(Product)

    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))

    products = query.all()

    # ✅ 카테고리별로 상품을 그룹화하여 반환
    result = {}
    for product in products:
        category = product.category or "기타"
        if category not in result:
            result[category] = []
        result[category].append({
            "id": product.id,
            "product_name": product.product_name,
            "barcode": product.barcode,
        })

    return result

def convert_product_to_kst(product: Product):
    """
    Product 객체의 날짜/시간 필드를 KST로 변환하여 반환
    """
    product_dict = ProductOut.model_validate(product).model_dump()
    product_dict["created_at"] = convert_utc_to_kst(product.created_at).isoformat()
    product_dict["updated_at"] = convert_utc_to_kst(product.updated_at).isoformat()
    return product_dict