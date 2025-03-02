from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    quantity = Column(Integer)
    unit_price = Column(Float)
    purchase_date = Column(Date)

    # product = relationship("Product", back_populates="purchases")  # ✅ 문자열로 참조 (해결됨)
