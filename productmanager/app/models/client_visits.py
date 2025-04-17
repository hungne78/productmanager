from sqlalchemy import Column, Integer, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
from app.db.base import Base
from app.utils.time_utils import convert_utc_to_kst
KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환하여 반환 """
    return datetime.now(KST)
def get_kst_today():
    return get_kst_now().date()
class ClientVisit(Base):
    __tablename__ = "client_visits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # ✅ KST로 저장
    visit_datetime = Column(DateTime(timezone=True), nullable=False, default=get_kst_now)


    visit_date = Column(Date, nullable=False, default=get_kst_today)  # ✅ 방문 날짜만 저장
    visit_count = Column(Integer, nullable=False, default=1)  # ✅ 방문 횟수 (초기값 1)


    # 관계 설정
    employee = relationship("Employee", back_populates="client_visits") 
    client = relationship("Client", back_populates="client_visits")
