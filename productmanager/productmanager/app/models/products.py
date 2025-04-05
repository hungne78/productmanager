# app/models/products.py
from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship, declared_attr
from app.db.base import Base
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    barcode = Column(String(50))
    default_price = Column(DECIMAL(10,2), default=0)
    incentive = Column(DECIMAL(10,2), default=0)
    stock = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    box_quantity = Column(Integer, nullable=False, default=1)
    category = Column(String(50), nullable=True)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # ✅ 상품의 가격 유형 (일반가 또는 고정가)
    is_fixed_price = Column(Boolean, default=False)  # True면 고정가, False면 일반가

    # ✅ 올바른 `back_populates` 매칭
    brand = relationship("Brand", back_populates="products")

    # ✅ OrderItem과의 관계 설정 (`back_populates` 수정)
    order_items = relationship("OrderItem", back_populates="product")

    # ✅ SalesRecord와의 관계 설정
    client_product_prices = relationship("ClientProductPrice", back_populates="product")
    sales = relationship("Sales", back_populates="product", cascade="all, delete-orphan")
    sales_records = relationship("SalesRecord", back_populates="product", cascade="all, delete-orphan")
    order_items_archive = relationship("OrderItemArchive", back_populates="product")
    inventory = relationship("EmployeeInventory", back_populates="product")
    barcodes = relationship("ProductBarcode", back_populates="product", cascade="all, delete-orphan")