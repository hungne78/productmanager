# app/models/purchase_archive.py

from sqlalchemy import Column, Integer, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")

def get_kst_today():
    """ 현재 날짜를 한국 시간(KST) 기준으로 반환 """
    return datetime.now(KST).date()

class PurchaseArchive(Base):
    __tablename__ = "purchases_archive"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Integer)
    unit_price = Column(Float)
    purchase_date = Column(Date, default=get_kst_today)

    # 단방향 참조
    product = relationship("Product")
