from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.purchases import Purchase
from app.models.products import Product
from app.schemas.purchases import PurchaseOut
from typing import List
from datetime import date, datetime
from pydantic import BaseModel
from app.utils.purchase_table_utils import get_purchase_model
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
    year = purchase_data.purchase_date.year
    Purchase = get_purchase_model(year)

    try:
        new_purchase = Purchase(
            product_id=purchase_data.product_id,
            quantity=purchase_data.quantity,
            unit_price=purchase_data.unit_price,
            purchase_date=purchase_data.purchase_date
        )
        db.add(new_purchase)

        product = db.query(Product).filter(Product.id == purchase_data.product_id).first()
        if product:
            product.stock += purchase_data.quantity
            db.commit()
            db.refresh(product)

        db.commit()
        db.refresh(new_purchase)
        return new_purchase

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"매입 등록 실패: {e}")



@router.get("/products/{product_id}/purchases")
def get_product_purchases(product_id: int, year: int = Query(None), db: Session = Depends(get_db)):
    year = year or datetime.now().year
    Purchase = get_purchase_model(year)

    return db.query(Purchase).filter(Purchase.product_id == product_id).all()


@router.get("/purchases", response_model=List[dict])
def list_purchases(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    year = (start_date or datetime.now().date()).year
    Purchase = get_purchase_model(year)

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
    year = purchase_data.purchase_date.year
    Purchase = get_purchase_model(year)

    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="매입 내역을 찾을 수 없습니다.")

    product = db.query(Product).filter(Product.id == purchase.product_id).first()
    if product:
        product.stock -= purchase.quantity
        product.stock += purchase_data.quantity

    purchase.product_id = purchase_data.product_id
    purchase.quantity = purchase_data.quantity
    purchase.unit_price = purchase_data.unit_price
    purchase.purchase_date = purchase_data.purchase_date

    db.commit()
    db.refresh(purchase)
    return {"message": "매입 내역 수정 성공", "purchase_id": purchase.id}


@router.delete("/purchases/{purchase_id}")
def delete_purchase(purchase_id: int, year: int = Query(None), db: Session = Depends(get_db)):
    year = year or datetime.now().year
    Purchase = get_purchase_model(year)

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
def get_monthly_purchases(product_id: int, year: int, db: Session = Depends(get_db)):
    from sqlalchemy import extract, func
    Purchase = get_purchase_model(year)

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
        m = int(row.purchase_month) - 1
        monthly_data[m] = int(row.sum_qty or 0)

    return monthly_data
