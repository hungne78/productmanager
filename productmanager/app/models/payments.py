# app/models/payments.py
from sqlalchemy import Column, BigInteger, Integer, DECIMAL, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # ✅ KST 기준으로 저장
    payment_date = Column(DateTime, default=get_kst_now)
    amount = Column(DECIMAL(12,2), default=0)
    payment_method = Column(String(20), default="cash")
    note = Column(String(255))

    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    client = relationship("Client", backref="payments") # optional
