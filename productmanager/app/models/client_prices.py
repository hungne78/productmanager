# app/models/client_prices.py
from sqlalchemy import Column, Integer, DECIMAL, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.db.base import Base

class ClientProductPrice(Base):
    __tablename__ = "client_product_prices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    special_price = Column(DECIMAL(10,2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("client_id", "product_id", name="uix_client_product"),
    )
