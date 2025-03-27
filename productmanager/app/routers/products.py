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
from app.models.brands import Brand

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

    brand_obj = db.query(Brand).filter(Brand.name == payload.brand_name).first()
    if not brand_obj:
        raise HTTPException(status_code=404, detail=f"브랜드 '{payload.brand_name}'를 찾을 수 없습니다.")
    
    new_product = Product(
        brand_id = brand_obj.id,
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
    """
    product_id 기준으로 상품 수정
    (역시 brand_name → brand.id 매핑)
    """
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    # 브랜드 이름 → ID 매핑
    brand_obj = db.query(Brand).filter(Brand.name == payload.brand_name).first()
    if not brand_obj:
        raise HTTPException(status_code=404, detail=f"브랜드 '{payload.brand_name}'를 찾을 수 없습니다.")

    # 필드 업데이트
    product.brand_id      = brand_obj.id
    product.product_name  = payload.product_name
    product.default_price = payload.default_price
    product.stock         = payload.stock
    product.is_active     = payload.is_active
    product.incentive     = payload.incentive
    product.box_quantity  = payload.box_quantity
    product.category      = payload.category
    product.is_fixed_price= payload.is_fixed_price
    product.updated_at    = get_kst_now()

    db.commit()
    db.refresh(product)

    # 바코드 재등록 (단순화: 일괄 삭제 후 재생성)
    db.query(ProductBarcode).filter(ProductBarcode.product_id == product_id).delete()
    db.commit()
    for code in payload.barcodes:
        clean_code = code.strip()
        if clean_code:
            db.add(ProductBarcode(product_id=product.id, barcode=clean_code))
    db.commit()
    db.refresh(product)

    return convert_product_to_kst(product)


# ======================================
# [PC 전용] 모든 상품 조회 라우트 (/manage)
# ======================================
@router.get("/manage", response_model=dict)
def get_products_for_pc(
    brand_name: Optional[str] = None,
    name: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    PC 앱에서 사용할 때: is_active 무관 모든 상품 조회
    brand_name(문자)로 필터 가능
    """
    query = db.query(Product)

    # (a) 브랜드 이름으로 필터
    if brand_name:
        brand_obj = db.query(Brand).filter(Brand.name == brand_name).first()
        if brand_obj:
            query = query.filter(Product.brand_id == brand_obj.id)
        else:
            return {}  # 해당 브랜드가 없다면 결과 없음

    # (b) 상품명 부분 검색
    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))

    # (c) 바코드 단일 검색 (products 테이블 barcode 필드가 아닌, product_barcodes 테이블도 고려해야 할 시는 수정)
    if barcode:
        # 만약 product_barcode 테이블 전부 확인하려면 join(ProductBarcode) -> filter(ProductBarcode.barcode==barcode)
        query = query.filter(Product.barcode == barcode)

    products = query.all()
    if not products:
        return {}

    # 카테고리별로 묶어서 반환
    categorized_products = defaultdict(list)
    for product in products:
        c = product.category or "미분류"
        p_dict = convert_product_to_kst(product)
        categorized_products[c].append(p_dict)

    return categorized_products


# ======================================
# [기타] 활성 상품만 조회 라우트 (/public)
# ======================================
@router.get("/public", response_model=dict)
def get_products_for_others(
    brand_name: Optional[str] = None,
    name: Optional[str] = None,
    barcode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    is_active=1 인 상품들만 조회
    brand_name(문자)로 필터 가능
    """
    query = db.query(Product).filter(Product.is_active == 1)

    if brand_name:
        brand_obj = db.query(Brand).filter(Brand.name == brand_name).first()
        if brand_obj:
            query = query.filter(Product.brand_id == brand_obj.id)
        else:
            return {}

    if name:
        query = query.filter(Product.product_name.ilike(f"%{name}%"))

    if barcode:
        query = query.filter(Product.barcode == barcode)

    products = query.all()
    if not products:
        return {}

    categorized_products = defaultdict(list)
    for product in products:
        c = product.category or "미분류"
        p_dict = convert_product_to_kst(product)
        categorized_products[c].append(p_dict)

    return categorized_products

# ======================================
# 필요에 따라: 바코드로 상품 찾기 (ProductBarcode 활용)
# ======================================
@router.get("/barcode/{barcode}", response_model=ProductOut)
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    여러 바코드를 지원하는 경우: product_barcodes 테이블에서 barcode를 찾고,
    연결된 product 반환
    """
    product_barcode = db.query(ProductBarcode).filter(ProductBarcode.barcode == barcode).first()
    if not product_barcode:
        raise HTTPException(status_code=404, detail="해당 바코드로 등록된 상품 없음")

    product = product_barcode.product
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
    
    return convert_product_to_kst(product)

# ======================================
# 카테고리별 브랜드별로 나눠서 조회(활성화 1로만)
# ======================================
@router.get("/grouped", response_model=dict)
def get_grouped_products(db: Session = Depends(get_db)):
    """
    모든 활성화 상품을 카테고리 → 브랜드별로 분류하여 반환
    """
    products = db.query(Product).filter(Product.is_active == 1).all()

    grouped = defaultdict(lambda: defaultdict(list))

    for product in products:
        category = product.category or "기타"
        brand_name = product.brand.name if product.brand else "기타"
        product_data = convert_product_to_kst(product)  # ✅ ProductOut 변환 포함
        grouped[category][brand_name].append(product_data)

    return grouped

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

########################################
# (9) 창고 재고 목록
########################################
@router.get("/warehouse_stock", response_model=List[dict])
def get_warehouse_stock(db: Session = Depends(get_db)):
    """
    창고 재고 목록
    """
    try:
        products = db.query(Product.id, Product.product_name, Product.stock).all()
        return [
            {
                "product_id": p.id,
                "product_name": p.product_name,
                "quantity": p.stock
            }
            for p in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 창고 재고 조회 실패: {str(e)}")


########################################
# (10) 재고 예약
########################################
@router.put("/{product_id}/reserve")
def reserve_product_stock(product_id: int, request: ReserveRequest, db: Session = Depends(get_db)):
    """
    재고를 예약 처리 (예: 출고/배차 등에서 임시로 빼놓는 개념)
    ※ 예시는 stock_reserved 필드가 있다고 가정
    """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        # stock_reserved 필드가 있다고 가정
        product.stock_reserved += request.quantity
        product.stock -= request.quantity
        db.commit()

    return {
        "message": "✅ 예약 성공",
        "new_stock": product.stock,
        "reserved_stock": product.stock_reserved
    }


########################################
# (11) 예약 취소
########################################
@router.put("/{product_id}/cancel_reservation")
def cancel_product_reservation(product_id: int, request: CancelReservationRequest, db: Session = Depends(get_db)):
    """
    재고 예약 취소
    """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        if product.stock_reserved < request.quantity:
            raise HTTPException(status_code=400, detail="🚨 예약된 재고 부족!")

        product.stock_reserved -= request.quantity
        product.stock += request.quantity
        db.commit()

    return {
        "message": "✅ 예약 취소 성공",
        "new_stock": product.stock,
        "reserved_stock": product.stock_reserved
    }


########################################
# (12) 모든 제품 재고 조회
########################################
@router.get("/stock")
def get_all_stock(db: Session = Depends(get_db)):
    """ 모든 제품의 최신 창고 재고 """
    products = db.query(Product).all()
    return [
        {
            "id": p.id,
            "stock": p.stock
        }
        for p in products
    ]


########################################
# (13) 재고 수동 수정
########################################
@router.put("/{product_id}/stock")
def update_product_stock(product_id: int, request: StockUpdateRequest, db: Session = Depends(get_db)):
    """
    stock_change (+/-)만큼 수량 증감
    """
    with db.begin():
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")

        new_total = product.stock + request.stock_change
        if new_total < 0:
            raise HTTPException(status_code=400, detail="🚨 재고 부족!")

        product.stock = new_total
        db.commit()

    return {
        "message": "✅ 재고 업데이트 성공",
        "new_stock": product.stock
    }


########################################
# (14) 6개월간 판매 X + 재고=0 => 자동삭제
########################################
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


########################################
# (15) 도우미 함수: Product → ProductOut
########################################
def convert_product_to_kst(product: Product) -> ProductOut:
    """
    DB의 Product 객체를 pydantic 모델로 변환 + KST 시간 + barcodes 리스트 등 처리
    - brand_name: product.brand.name
    - barcodes: product_barcodes 테이블
    - created_at, updated_at: KST 변환
    """
    # 바코드들
    if hasattr(product, "barcodes"):
        barcode_list = [b.barcode for b in product.barcodes]
    else:
        barcode_list = []

    # KST 변환
    created_kst = convert_utc_to_kst(product.created_at) if product.created_at else None
    updated_kst = convert_utc_to_kst(product.updated_at) if product.updated_at else None

    # brand_name
    brand_name = product.brand.name if product.brand else "알수없음"

    return ProductOut(
        id = product.id,
        brand_name = brand_name,
        product_name = product.product_name,
        barcodes = barcode_list,
        default_price = float(product.default_price or 0),
        incentive = float(product.incentive or 0),
        stock = product.stock,
        box_quantity = product.box_quantity,
        category = product.category,
        is_active = product.is_active,
        is_fixed_price = product.is_fixed_price,
        created_at = created_kst,
        updated_at = updated_kst
    )