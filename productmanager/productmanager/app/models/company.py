from sqlalchemy import Column, Integer, String
from app.db.base import Base

class CompanyInfo(Base):
    __tablename__ = "company_info"

    id = Column(Integer, primary_key=True, autoincrement=True)  # ✅ 기본 키 추가
    company_name = Column(String(100), nullable=False)
    ceo_name = Column(String(50), nullable=False)
    address = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    business_number = Column(String(20), nullable=False)
    bank_account = Column(String(50), nullable=False)
