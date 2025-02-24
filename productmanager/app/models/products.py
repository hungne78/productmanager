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
    incentive = Column(DECIMAL(10,2), default=0)
    stock = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    box_quantity = Column(Integer, nullable=False, default=1)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ✅ 올바른 `back_populates` 매칭
    brand = relationship("Brand", back_populates="products")

    # ✅ OrderItem과의 관계 설정 (`back_populates` 수정)
    order_items = relationship("OrderItem", back_populates="product")

    # ✅ SalesRecord와의 관계 설정
    sales_records = relationship("SalesRecord", back_populates="product")
    client_product_prices = relationship("ClientProductPrice", back_populates="product")