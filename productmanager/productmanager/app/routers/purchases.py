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
    """ 매입 등록 시 상품 재고 업데이트 (KST로 저장) """
    print(f"📡 매입 등록 요청 데이터 (서버): {purchase_data.dict()}")  

    try:
        new_purchase = Purchase(
            product_id=purchase_data.product_id,
            quantity=purchase_data.quantity,
            unit_price=purchase_data.unit_price,
            purchase_date=purchase_data.purchase_date  # ✅ 변환 제거
        )
        db.add(new_purchase)

        product = db.query(Product).filter(Product.id == purchase_data.product_id).first()
        if product:
            product.stock += purchase_data.quantity  
            db.commit()
            db.refresh(product)

        db.commit()
        db.refresh(new_purchase)

        return new_purchase  # ✅ 변환 없이 그대로 반환

    except Exception as e:
        db.rollback()
        print(f"❌ 매입 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"매입 등록 실패: {e}")


@router.get("/products/{product_id}/purchases")
def get_product_purchases(product_id: int, db: Session = Depends(get_db)):
    """ 특정 상품의 모든 매입 내역 조회 (KST 변환 없음) """
    return db.query(Purchase).filter(Purchase.product_id == product_id).all()  # ✅ 변환 없이 반환

@router.get("/purchases", response_model=List[dict])
def list_purchases(db: Session = Depends(get_db), start_date: date = Query(None), end_date: date = Query(None)):
    """ 매입 내역 조회 (상품명 포함, KST 변환 없음) """
    query = db.query(
        Purchase.id,
        Purchase.product_id,
        Purchase.quantity,
        Purchase.unit_price,
        Purchase.purchase_date,
        Product.product_name  
    ).join(Product, Product.id == Purchase.product_id)

    if start_date:
        query = query.filter(Purchase.purchase_date >= start_date)
    if end_date:
        query = query.filter(Purchase.purchase_date <= end_date)

    purchases = query.all()

    return [
        {
            "id": p.id,
            "product_id": p.product_id,
            "quantity": p.quantity,
            "unit_price": p.unit_price,
            "purchase_date": p.purchase_date,
            "product_name": p.product_name
        }
        for p in purchases
    ]

@router.put("/purchases/{purchase_id}")
def update_purchase(purchase_id: int, purchase_data: PurchaseUpdate, db: Session = Depends(get_db)):
    """ 매입 수정 시 재고 업데이트 """
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="매입 내역을 찾을 수 없습니다.")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if product:
        product.stock -= purchase.quantity  # ✅ 기존 수량 차감
        product.stock += purchase_data.quantity  # ✅ 새 수량 추가

    purchase.product_id = purchase_data.product_id
    purchase.quantity = purchase_data.quantity
    purchase.unit_price = purchase_data.unit_price
    purchase.purchase_date = purchase_data.purchase_date

    db.commit()
    db.refresh(purchase)
    return {"message": "매입 내역 수정 성공", "purchase_id": purchase.id}

@router.delete("/purchases/{purchase_id}")
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """ 매입 내역 삭제 시 재고 감소 """
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="매입 내역을 찾을 수 없습니다.")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if product:
        product.stock -= purchase.quantity  

    db.delete(purchase)
    db.commit()
    return {"message": "매입 내역 삭제 성공"}


@router.get("/purchases/monthly_purchases/{product_id}/{year}")
def get_monthly_purchases(
    product_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    특정 상품(product_id)에 대해, 해당 연도(year)의 월별 매입수량 합계를 [1..12] 리스트 형태로 반환
    예: [10, 0, 5, 20, 0, ...] (12개)
    """
    from sqlalchemy import extract, func

    results = (
        db.query(
            extract('month', Purchase.purchase_date).label('purchase_month'),
            func.sum(Purchase.quantity).label('sum_qty')
        )
        .filter(Purchase.product_id == product_id)
        .filter(extract('year', Purchase.purchase_date) == year)
        .group_by(extract('month', Purchase.purchase_date))
        .all()
    )

    monthly_data = [0]*12
    for row in results:
        m = int(row.purchase_month) - 1  # 1월이면 index=0
        monthly_data[m] = int(row.sum_qty or 0)

    return monthly_data
