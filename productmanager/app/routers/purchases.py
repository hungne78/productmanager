from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.purchases import Purchase
from app.models.products import Product
from app.schemas.purchases import PurchaseOut
from typing import List

router = APIRouter()

@router.get("/products/{product_id}/purchases")
def get_product_purchases(product_id: int, db: Session = Depends(get_db)):
    result = db.query(Purchase).filter(Purchase.product_id == product_id).all()
    return result


@router.get("/purchases")
def list_purchases(db: Session = Depends(get_db)):
    """
    Return all purchase records.
    """
    purchases = db.query(Purchase).all()
    return purchases