from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_today():
    """ 현재 날짜를 한국 시간(KST) 기준으로 반환 """
    return datetime.now(KST).date()

class OrderArchive(Base):
    __tablename__ = "orders_archive"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)  
    order_date = Column(Date, default=get_kst_today)  
    status = Column(String(50), default="pending")  
    total_amount = Column(Float, default=0.0)  
    total_incentive = Column(Float, default=0.0)  
    total_boxes = Column(Integer, default=0)  

    # 관계 설정
    employee = relationship("Employee", back_populates="orders_archive")
    order_items = relationship("OrderItemArchive", back_populates="order", cascade="all, delete-orphan")

class OrderItemArchive(Base):
    __tablename__ = "order_items_archive"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders_archive.id", ondelete="CASCADE"), nullable=False)  
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  
    quantity = Column(Integer, default=1)  

    # 관계 설정
    order = relationship("OrderArchive", back_populates="order_items")
    product = relationship("Product", back_populates="order_items_archive")
