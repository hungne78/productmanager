# app/models/franchise_order_archive.py

from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.utils.time_utils import get_kst_now

class FranchiseOrderArchive(Base):
    __tablename__ = "franchise_orders_archive"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    order_date = Column(Date, nullable=False)
    shipment_round = Column(Integer, default=0)
    is_transferred = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_kst_now)

    items = relationship("FranchiseOrderItemArchive", back_populates="franchise_order")


class FranchiseOrderItemArchive(Base):
    __tablename__ = "franchise_order_items_archive"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("franchise_orders_archive.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer, nullable=False)

    franchise_order = relationship("FranchiseOrderArchive", back_populates="items")
    product = relationship("Product")
