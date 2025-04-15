# app/models/admin_users.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
import pytz
from app.db.base import Base

KST = pytz.timezone("Asia/Seoul")

def get_kst_now():
    return datetime.now(KST)

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(String(20), default="admin")  # 어드민 권한
    created_at = Column(DateTime, default=get_kst_now)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)
