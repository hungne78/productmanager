# app/routers/products.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from collections import defaultdict
from dateutil.relativedelta import relativedelta


from app.models.products import Product
from app.models.product_barcodes import ProductBarcode
from app.models.sales_records import SalesRecord
from app.schemas.products import ProductCreate, ProductOut, ProductResponse, ProductUpdate
from app.utils.time_utils import get_kst_now, convert_utc_to_kst
from app.db.database import get_db  # SessionLocal() 반환


router = APIRouter()


# ======================================
# 요청 바디용 Pydantic 모델
# ======================================
class StockUpdateRequest(BaseModel):
    stock_change: int

class ReserveRequest(BaseModel):
    quantity: int

class CancelReservationRequest(BaseModel):
    quantity: int

# ======================================
# 상품 등록
# ======================================
@router.post("/", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(
        brand_id=payload.brand_id,
        product_name=payload.product_name,
        
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
    for code in payload.barcodes:
        if code.strip():
            db.add(ProductBarcode(product_id=new_product.id, barcode=code.strip()))
    db.commit()

    db.refresh(new_product)
    return convert_product_to_kst(new_product)

# ======================================
# 상품 수정 (예: product_id로 Update)
# ======================================
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
    product.updated_at = get_kst_now()

    db.commit()
    db.refresh(product)
    return convert_product_to_kst(product)

# ======================================
# [PC 전용] 모든 상품 조회 라우트 (/manage)
# ======================================
@router.get("/manage", response_model=dict)
def get_products_for_pc(
    brand_id: Optional[int] = None,
    name: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    PC앱 전용: is_active 무관 (모든 상품) 조회
    """
    query = db.query(Product)
    if brand_id is not None:
        query = query.filter(Product.brand_id == brand_id)
    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))
    if barcode:
        query = query.filter(Product.barcode == barcode)

    products = query.all()
    if not products:
        return {}

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
            "is_fixed_price": product.is_fixed_price
        })
    return categorized_products


# ======================================
# [기타] 활성 상품만 조회 라우트 (/public)
# ======================================
@router.get("/public", response_model=dict)
def get_products_for_others(
    brand_id: Optional[int] = None,
    name: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    기타 (플러터, 주문, 매출 등)에서 사용할: is_active=1 상품만 조회
    """
    query = db.query(Product).filter(Product.is_active == 1)

    if brand_id is not None:
        query = query.filter(Product.brand_id == brand_id)
    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))
    if barcode:
        query = query.filter(Product.barcode == barcode)

    products = query.all()
    if not products:
        return {}

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
            "is_fixed_price": product.is_fixed_price
        })
    return categorized_products

# ======================================
# 필요에 따라: 바코드로 상품 찾기 (ProductBarcode 활용)
# ======================================
@router.get("/barcode/{barcode}", response_model=ProductOut)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    여러 바코드 → 하나의 상품 구조 시, product_barcodes 테이블에서 barcode를 찾아 product_id 연결
    """
    product_barcode = db.query(ProductBarcode).filter(ProductBarcode.barcode == barcode).first()
    if not product_barcode:
        raise HTTPException(status_code=404, detail="해당 바코드의 상품이 없습니다.")
    
    product = product_barcode.product
    if not product:
        raise HTTPException(status_code=404, detail="Product not found for this barcode")
    
    return convert_product_to_kst(product)

# ======================================
# 상품 삭제
# ======================================
@router.delete("/name/{product_name}")
def delete_product_by_name(product_name: str, db: Session = Depends(get_db)):
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

# ======================================
# 기타 재고 관련 API
# ======================================
@router.get("/warehouse_stock", response_model=List[dict])
def get_warehouse_stock(db: Session = Depends(get_db)):
    """
    창고 재고 목록
    """
    try:
        products = db.query(Product.id, Product.product_name, Product.stock).all()
        return [
            {"product_id": p.id, "product_name": p.product_name, "quantity": p.stock} 
            for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 창고 재고 조회 실패: {str(e)}")

@router.put("/{product_id}/reserve")
def reserve_product_stock(product_id: int, request: ReserveRequest, db: Session = Depends(get_db)):
    """ 재고 예약 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock_reserved += request.quantity
        product.stock -= request.quantity
        db.commit()

    return {"message": "✅ 예약 성공", "new_stock": product.stock, "reserved_stock": product.stock_reserved}

@router.put("/{product_id}/cancel_reservation")
def cancel_product_reservation(product_id: int, request: CancelReservationRequest, db: Session = Depends(get_db)):
    """ 재고 예약 취소 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock_reserved < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 예약된 재고 부족!")

        product.stock_reserved -= request.quantity
        product.stock += request.quantity
        db.commit()

    return {"message": "✅ 예약 취소 성공", "new_stock": product.stock, "reserved_stock": product.stock_reserved}

@router.get("/stock")
def get_all_stock(db: Session = Depends(get_db)):
    """ 모든 제품의 최신 창고 재고 """
    products = db.query(Product).all()
    return [{"id": p.id, "stock": p.stock} for p in products]

@router.put("/{product_id}/stock")
def update_product_stock(product_id: int, request: StockUpdateRequest, db: Session = Depends(get_db)):
    """ 재고 수동 수정 """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        new_total = product.stock + request.stock_change
        if new_total < 0:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock = new_total
        db.commit()
    return {"message": "✅ 재고 업데이트 성공", "new_stock": product.stock}

# ======================================
# 6개월간 판매 X + 재고=0 → 자동 삭제
# ======================================
@router.post("/cleanup_unused")
def cleanup_unused_products(db: Session = Depends(get_db)):
    six_months_ago = get_kst_now() - relativedelta(months=6)
    recent_sold_subq = (
        db.query(SalesRecord.product_id)
        .filter(SalesRecord.sale_datetime >= six_months_ago)
        .distinct()
        .subquery()
    )
    unused_products = (
        db.query(Product)
        .filter(Product.stock == 0)
        .filter(~Product.id.in_(recent_sold_subq))
        .all()
    )
    count = len(unused_products)
    for p in unused_products:
        db.delete(p)
    db.commit()

    return {"deleted_count": count, "detail": f"{count}개 상품 삭제됨"}


# ======================================
# 도우미 함수
# ======================================
def convert_product_to_kst(product: Product):
    """ Product 객체의 날짜/시간(KST) 변환 """
    product_dict = ProductOut.model_validate(product).model_dump()
    product_dict["created_at"] = convert_utc_to_kst(product.created_at).isoformat()
    product_dict["updated_at"] = convert_utc_to_kst(product.updated_at).isoformat()
    # ✅ 바코드 리스트 변환
    product_dict["barcodes"] = [b.barcode for b in product.barcodes] if hasattr(product, "barcodes") else []
    return product_dict
