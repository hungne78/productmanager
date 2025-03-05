from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)

class ClientVisit(Base):
    __tablename__ = "client_visits"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # ✅ KST로 저장
    visit_datetime = Column(DateTime, nullable=False, default=get_kst_now)

    # ✅ 생성/수정 시간도 KST로 저장
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)

    # 관계 설정
    employee = relationship("Employee", back_populates="client_visits") 
    client = relationship("Client", back_populates="client_visits")
