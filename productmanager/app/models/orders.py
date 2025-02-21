# app/models/orders.py
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    DECIMAL,
    DateTime,
    String,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.now)
    total_amount = Column(DECIMAL(12,2), default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order_items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(10,2), nullable=False, default=0)
    line_total = Column(DECIMAL(12,2), nullable=False, default=0)
    # 추가: incentive 필드 (절대 금액, 인센티브)
    incentive = Column(DECIMAL(10,2), nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    order = relationship("Order", back_populates="order_items")
