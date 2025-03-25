# models/product_barcodes.py (새 파일) or 같은 파일 안에

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ProductBarcode(Base):
    __tablename__ = "product_barcodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    barcode = Column(String(50), nullable=False, index=True)

    # 관계
    product = relationship("Product", back_populates="barcodes")
