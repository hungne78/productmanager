# app/models/lent.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime
from pytz import timezone

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)

class Lent(Base):
    __tablename__ = "lents"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    brand = Column(String(255), nullable=False)           # 단순 상표 이름
    serial_number = Column(String(255), nullable=False)     # 시리얼 번호
    year = Column(Integer, nullable=False)                  # 년식
    
    # ✅ KST 기준으로 생성/수정 시간 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)
    
    # 필요하다면 Client와의 관계 설정도 추가 가능:
    client = relationship("Client", back_populates="lents")
