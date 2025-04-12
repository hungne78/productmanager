from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
from pytz import timezone

KST = timezone("Asia/Seoul")

def get_kst_today():
    return datetime.now(KST).date()

class ProductPurchasePrice(Base):
    __tablename__ = "product_purchase_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    purchase_price = Column(DECIMAL(10, 2), nullable=False)
    start_date = Column(Date, nullable=False, default=get_kst_today)  # KST 기준 기본값
    end_date = Column(Date, nullable=True)

    product = relationship("Product", back_populates="purchase_prices")
