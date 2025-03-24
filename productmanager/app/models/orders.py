from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")


def get_kst_today():
    """ 현재 날짜를 한국 시간(KST) 기준으로 반환 """
    return datetime.now(KST).date()

# ✅ 1️⃣ 주문 종료 테이블 추가
class OrderLock(Base):
    __tablename__ = "order_locks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lock_date = Column(Date, unique=True, nullable=False)  # ✅ 특정 날짜의 주문 잠금 여부
    is_locked = Column(Boolean, default=False)  # ✅ 기본값: False (주문 수정 가능)
    is_finalized = Column(Boolean, default=False)  # ✅ 기본값: False (출고 확정 여부)
    
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)  # ✅ 직원 ID 유지
    order_date = Column(Date, default=get_kst_today)  # ✅ 주문 날짜 유지
    status = Column(String(50), default="pending")  # ✅ 주문 상태 유지
    total_amount = Column(Float, default=0.0)  # ✅ 총 금액 (order_items에서 계산 후 저장)
    total_incentive = Column(Float, default=0.0)  # ✅ 총 인센티브 (order_items에서 계산 후 저장)
    total_boxes = Column(Integer, default=0)  # ✅ 총 박스 수량 (order_items에서 계산 후 저장)
    shipment_round = Column(Integer, default=0)
    
    # 관계 설정
    employee = relationship("Employee", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)  # ✅ 주문 ID 유지
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # ✅ 상품 ID 유지
    quantity = Column(Integer, nullable=False)  # ✅ 수량 유지

    # 관계 설정
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
