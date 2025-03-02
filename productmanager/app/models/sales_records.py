# app/models/sales_records.py
from sqlalchemy import Column, BigInteger, Integer, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)  # ✅ 자동 증가 추가
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)  # 거래처 ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # 제품 ID
    quantity = Column(Integer, default=0)  # 판매 수량
    sale_date = Column(Date, nullable=False)  # 판매 날짜
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 관계
    client = relationship("Client", back_populates="sales_records") 
    product = relationship("Product", back_populates="sales_records")
    employee = relationship("Employee", back_populates="sales_records", lazy="joined", cascade="all, delete")