# models/category_price_override.py

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class CategoryPriceOverride(Base):
    __tablename__ = "category_price_overrides"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    category_name = Column(String(255), nullable=False)
    price_type = Column(String(255), nullable=False)  # "normal" 또는 "fixed"
    override_price = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    client = relationship("Client", back_populates="category_overrides")
