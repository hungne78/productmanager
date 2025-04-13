# app/routers/admin_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.database import get_db
from app.models.admin_users import AdminUser
from app.schemas.admin_users import AdminUserCreate, AdminUserLogin, AdminUserOut
from app.core.security import create_access_token
from datetime import timedelta

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register", response_model=AdminUserOut)
def create_admin_user(payload: AdminUserCreate, db: Session = Depends(get_db)):
    # 이메일 중복 체크
    existing = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    
    hashed_pw = get_password_hash(payload.password)
    new_admin = AdminUser(
        email=payload.email,
        password_hash=hashed_pw,
        name=payload.name,
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.post("/login")
def login_admin_user(payload: AdminUserLogin, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    # 토큰 발행 (기본 1년)
    access_token_expires = None  # None -> 1년
    # 만약 2주로 하고 싶다면: access_token_expires = timedelta(days=14)
    access_token = create_access_token(
        data={"sub": user.email, "admin_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }
