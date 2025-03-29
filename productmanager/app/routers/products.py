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
import os
from app.models.products import Product

from app.models.products import Product
from app.models.product_barcodes import ProductBarcode
from app.models.sales_records import SalesRecord
from app.schemas.products import ProductCreate, ProductOut, ProductResponse, ProductUpdate
from app.utils.time_utils import get_kst_now, convert_utc_to_kst
from app.db.database import get_db  # SessionLocal() 반환
from collections import defaultdict, OrderedDict
import json
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
    from collections import defaultdict, OrderedDict
    import os, json

    # 🔹 (1) 모든 상품 불러오기
    products = (
        db.query(Product)
        .filter(Product.is_active == 1, Product.product_name.isnot(None), Product.product_name != "")
        .all()
    )

    # 🔹 (2) temp_dict: category → list of (brand_id, brand_name, product_dict)
    temp_dict = defaultdict(list)
    # 디버깅 삽입 (for문 위)
    # print(f"📦 정렬 대상 브랜드 목록: {[x[1] for x in items]}")
    # print(f"📘 브랜드 정렬 기준 brand_order_dict: {brand_order_dict}")

    for product in products:
        category = product.category or "기타"
        brand_id = product.brand_id if product.brand_id is not None else 9999
        brand_name = product.brand.name if product.brand else "기타"

        product_data = convert_product_to_kst(product)
        product_dict = dict(product_data)
        product_dict["brand_name"] = brand_name  # UI에서 사용

        temp_dict[category].append((brand_id, brand_name, product_dict))

    # 🔹 (3) 카테고리 순서 로드
    category_order = []
    if os.path.exists("category_order_server.json"):
        with open("category_order_server.json", "r", encoding="utf-8") as f:
            category_order = json.load(f)

    # 🔹 (4) 브랜드 순서 로드
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    brand_order_path = os.path.join(BASE_DIR, "brand_order_server.json")

    brand_order = []
    if os.path.exists(brand_order_path):
        with open(brand_order_path, "r", encoding="utf-8") as f:
            brand_order = json.load(f)
            print(f"{brand_order}")

    brand_order_dict = {name.strip(): idx for idx, name in enumerate(brand_order)}


    # 🔹 (5) 최종 그룹화된 결과
    grouped = OrderedDict()

    # ✅ (5-1) 지정된 카테고리 순서에 따라 처리
    for category in category_order:
        if category in temp_dict:
            items = temp_dict[category]
            ordered_brand_group = OrderedDict()
            for bid, bname, pdata in sorted(items, key=lambda x: brand_order_dict.get(x[1].strip(), 9999)):
                clean_name = bname.strip()
                ordered_brand_group.setdefault(clean_name, []).append(pdata)
            
            # 🔠 정렬 추가 (이 아래 for문 끝나고 정렬 적용)
            for brand in ordered_brand_group:
                ordered_brand_group[brand].sort(key=lambda p: p["product_name"])
                
            grouped[category] = ordered_brand_group
    

    # ✅ (5-2) 누락된 카테고리 처리 (카테고리 정렬 외에 추가된 것들)
    remaining_categories = sorted(set(temp_dict.keys()) - set(category_order))
    for category in remaining_categories:
        items = temp_dict[category]
        brand_group = defaultdict(list)

        for bid, bname, pdata in sorted(items, key=lambda x: brand_order_dict.get(x[1], 9999)):
            brand_group[bname].append(pdata)

        grouped[category] = brand_group

    return grouped





# ======================================
# 모든 카테고리 반환
# ======================================

@router.get("/categories", response_model=List[str])
def get_all_categories(db: Session = Depends(get_db)):
    """
    활성화된 상품의 고유 카테고리 목록 반환 (중복 제거, None → '기타')
    """
    categories = (
        db.query(Product.category)
        .filter(Product.is_active == 1)
        .distinct()
        .all()
    )
    category_names = {c[0] or "기타" for c in categories}
    return sorted(category_names)
# ======================================
# 브랜드정렬
# ======================================

@router.get("/brands", response_model=List[str])
def get_all_brands(db: Session = Depends(get_db)):
    """
    활성화된 상품의 브랜드 이름 목록 반환 (중복 제거, None → '기타')
    """
    products = (
        db.query(Product)
        .filter(Product.is_active == 1)
        .all()
    )

    names = {p.brand.name if p.brand else "기타" for p in products}
    return sorted(names)

@router.get("/brands/order", response_model=List[str])
def get_brand_order():
    import os, json
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand_order_server.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@router.post("/brands/order")
def save_brand_order(order: List[str]):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(BASE_DIR, "brand_order_server.json")

    print(f"🔹 [DEBUG] save_brand_order(): order={order}")
    print(f"🔹 [DEBUG] save_path={save_path}")

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(order, f, ensure_ascii=False)
    print("✅ 브랜드 순서 저장 완료")

    return {"message": "브랜드 순서 저장 완료"}

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
    
class CategoryOrderRequest(BaseModel):
    order: List[str]

@router.post("/category_order")
def save_category_order(req: CategoryOrderRequest):
    category_order = req.order
    # 예: 서버에 파일로 저장하거나 DB 저장
    with open("category_order_server.json", "w", encoding="utf-8") as f:
        json.dump(category_order, f, ensure_ascii=False, indent=2)
    return {"message": "서버에 카테고리 순서 저장 완료"}
