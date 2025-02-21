# app/models/sales_records.py
from sqlalchemy import Column, BigInteger, Integer, DECIMAL, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=0)
    unit_price = Column(DECIMAL(10,2), default=0)
    total_amount = Column(DECIMAL(12,2), default=0)
    sale_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
