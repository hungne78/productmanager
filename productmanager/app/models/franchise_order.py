from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class FranchiseOrder(Base):
    __tablename__ = "franchise_orders"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    order_date = Column(Date, nullable=False)
    shipment_round = Column(Integer, default=0)
    is_transferred = Column(Boolean, default=False)  # 서버 전송 여부
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("FranchiseOrderItem", back_populates="franchise_order")


class FranchiseOrderItem(Base):
    __tablename__ = "franchise_order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("franchise_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    franchise_order = relationship("FranchiseOrder", back_populates="items")
    product = relationship("Product")
