from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employees import Employee
from app.schemas.employees import EmployeeLogin, EmployeeLoginResponse, EmployeeOut
from app.core.security import verify_password, create_access_token
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from datetime import datetime
from jose import JWTError, jwt

auth_router = APIRouter()


@auth_router.post("/login", response_model=EmployeeLoginResponse)
def login_employee(payload: EmployeeLogin, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == payload.id).first()
    if not emp:
        raise HTTPException(status_code=401, detail="Invalid employee id.")
    if not verify_password(payload.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password.")

    token_data = {"sub": str(emp.id)}
    token = create_access_token(data=token_data)
    return EmployeeLoginResponse(
        id=emp.id,
        name=emp.name,
        phone=emp.phone,
        role=emp.role,
        token=token
    )
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"🔹 [DEBUG] 받은 토큰: {token}")
    print(f"🔹 [DEBUG] 서버의 SECRET_KEY: {settings.SECRET_KEY}, ALGORITHM: {settings.ALGORITHM}")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        exp_time = payload.get("exp")

        print(f"🔹 [DEBUG] 토큰 해독됨: user_id={user_id}, exp={exp_time}")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError as e:
        print(f"❌ [ERROR] JWT 해독 실패: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(Employee).filter(Employee.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    print(f"🔹 [DEBUG] 인증된 사용자 정보: ID={user.id}, Name={user.name}, Role={user.role}")  # ✅ role 값 확인

    return EmployeeOut(
        id=user.id,
        name=user.name,
        phone=user.phone,
        role=user.role
    )
