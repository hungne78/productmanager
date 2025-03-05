from sqlalchemy import Column, Integer, Float, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

def get_kst_today():
    """ 현재 날짜를 한국 시간(KST) 기준으로 반환 """
    return get_kst_now().date()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(String(50), default="pending")

    # ✅ KST 기준으로 저장
    order_date = Column(Date, default=get_kst_today)
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    client = relationship("Client", back_populates="orders")
    employee = relationship("Employee", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    line_total = Column(Float, default=0.0)
    incentive = Column(Float, default=0.0)

    # ✅ KST 기준으로 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
