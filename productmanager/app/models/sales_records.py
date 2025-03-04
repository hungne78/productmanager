# app/models/sales_records.py
from sqlalchemy import Column, BigInteger, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)  # ✅ 자동 증가 추가
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)  # 거래처 ID
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)  # 제품 ID
    quantity = Column(Integer, default=0)  # 판매 수량

    # ✅ KST 기준으로 판매 날짜 저장
    sale_datetime = Column(DateTime, nullable=False, default=get_kst_now)

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계
    client = relationship("Client", back_populates="sales_records") 
    product = relationship("Product", back_populates="sales_records")
    employee = relationship("Employee", back_populates="sales_records", lazy="joined", cascade="all, delete")
