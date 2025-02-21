# app/models/products.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    barcode = Column(String(50))
    default_price = Column(DECIMAL(10,2), default=0)
    incentive = Column(DECIMAL(10,2), default=0)  # 추가: 상품별 인센티브 (절대 금액)
    stock = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # "brand"와 연결
    brand = relationship("Brand", back_populates="products")