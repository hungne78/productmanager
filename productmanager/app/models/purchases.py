from sqlalchemy import Column, Integer, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
from pytz import timezone

def get_kst_today():
    """ 현재 날짜를 한국 시간(KST) 기준으로 반환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst).date()

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, index=True)
    quantity = Column(Integer)
    unit_price = Column(Float)

    # ✅ KST 기준으로 구매 날짜 저장
    purchase_date = Column(Date, default=get_kst_today)

    # product = relationship("Product", back_populates="purchases")  # ✅ 문자열로 참조 (해결됨)
