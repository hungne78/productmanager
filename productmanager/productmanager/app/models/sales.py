# app/models/sales.py (모델 파일)
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    return datetime.now(KST)

class Sales(Base):
    __tablename__ = "sales"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product = relationship("Product", back_populates="sales")

    category = Column(String(50), nullable=True)  # 카테고리
    total_quantity = Column(Integer, nullable=True, default=0)  # 해당 카테고리의 총 수량
    total_amount = Column(Float, nullable=True, default=0.0)  # 해당 카테고리의 총 금액

    # ✅ 반품 금액 추가
    return_amount = Column(Float, nullable=False, default=0.0)  # 반품 금액 추가
    
    # ✅ KST 기준으로 판매 시간 저장
    sale_datetime = Column(DateTime, default=get_kst_now)

    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # 관계 설정
    employee = relationship("Employee", back_populates="sales")
    client = relationship("Client", back_populates="sales")
