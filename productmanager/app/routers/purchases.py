from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.purchases import Purchase
from app.models.products import Product
from app.schemas.purchases import PurchaseOut
from typing import List
from datetime import date
from pydantic import BaseModel
router = APIRouter()

class PurchaseCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    purchase_date: date

class PurchaseUpdate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    purchase_date: date
@router.post("/purchases")
def create_purchase(purchase_data: PurchaseCreate, db: Session = Depends(get_db)):
    """
    매입 등록 시 상품 재고 업데이트
    """
    print(f"📡 매입 등록 요청 데이터 (서버): {purchase_data.dict()}")  

    try:
        # ✅ 매입 데이터 추가
        new_purchase = Purchase(
            product_id=purchase_data.product_id,
            quantity=purchase_data.quantity,
            unit_price=purchase_data.unit_price,
            purchase_date=purchase_data.purchase_date
        )
        db.add(new_purchase)

        # ✅ 재고 업데이트 (상품 테이블에서 stock 증가)
        product = db.query(Product).filter(Product.id == purchase_data.product_id).first()
        if product:
            product.stock += purchase_data.quantity  # ✅ 기존 재고에 추가
            db.commit()
            db.refresh(product)

        db.commit()
        db.refresh(new_purchase)
        print(f"✅ 매입 등록 및 재고 업데이트 완료: {new_purchase}")
        return {"message": "매입 등록 성공", "purchase_id": new_purchase.id}

    except Exception as e:
        db.rollback()
        print(f"❌ 매입 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"매입 등록 실패: {e}")

    
@router.get("/products/{product_id}/purchases")
def get_product_purchases(product_id: int, db: Session = Depends(get_db)):
    result = db.query(Purchase).filter(Purchase.product_id == product_id).all()
    return result


@router.get("/purchases", response_model=List[dict])
def list_purchases(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    """
    매입 내역 조회 (상품명 포함)
    """
    query = db.query(
        Purchase.id,
        Purchase.product_id,
        Purchase.quantity,
        Purchase.unit_price,
        Purchase.purchase_date,
        Product.product_name  # ✅ 상품명 추가
    ).join(Product, Product.id == Purchase.product_id)

    # 날짜 필터링 추가
    if start_date:
        query = query.filter(Purchase.purchase_date >= start_date)
    if end_date:
        query = query.filter(Purchase.purchase_date <= end_date)

    purchases = query.all()

    # ✅ 반환 데이터 수정하여 상품명을 포함
    result = [
        {
            "id": purchase.id,
            "product_id": purchase.product_id,
            "quantity": purchase.quantity,
            "unit_price": purchase.unit_price,
            "purchase_date": purchase.purchase_date,
            "product_name": purchase.product_name  # ✅ 상품명 반환
        }
        for purchase in purchases
    ]

    print(f"📡 반환 데이터: {result}")  # ✅ FastAPI에서 반환되는 데이터 확인
    return result

@router.put("/purchases/{purchase_id}")
def update_purchase(purchase_id: int, purchase_data: PurchaseUpdate, db: Session = Depends(get_db)):
    """
    매입 수정 시 재고 업데이트
    """
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="매입 내역을 찾을 수 없습니다.")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if product:
        product.stock -= purchase.quantity  # ✅ 기존 수량 차감
        product.stock += purchase_data.quantity  # ✅ 새 수량 추가

    # ✅ 매입 데이터 업데이트
    purchase.product_id = purchase_data.product_id
    purchase.quantity = purchase_data.quantity
    purchase.unit_price = purchase_data.unit_price
    purchase.purchase_date = purchase_data.purchase_date

    db.commit()
    db.refresh(purchase)
    return {"message": "매입 내역 수정 성공", "purchase_id": purchase.id}


@router.delete("/purchases/{purchase_id}")
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """
    매입 내역 삭제 시 재고 감소
    """
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="매입 내역을 찾을 수 없습니다.")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if product:
        product.stock -= purchase.quantity  # ✅ 기존 재고에서 매입 수량만큼 차감

    db.delete(purchase)
    db.commit()
    return {"message": "매입 내역 삭제 성공"}

