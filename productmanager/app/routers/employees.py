# app/routers/employees.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from typing import List
from app.db.database import get_db
from jose import jwt, JWTError
from app.models.employees import Employee
from app.schemas.employees import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeLogin,
    EmployeeLoginResponse
)
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.employee_clients import EmployeeClient
from app.schemas.clients import ClientOut
from sqlalchemy.orm import joinedload
from app.models.employee_vehicle import EmployeeVehicle
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/employees/login") 

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Employee).filter(Employee.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

router = APIRouter()

@router.get("/{emp_id}/clients", response_model=List[ClientOut])
def get_employee_clients(emp_id: int, db: Session = Depends(get_db)):
    """ 특정 사원이 담당하는 거래처 목록 조회 """
    emp = db.query(Employee)\
        .options(joinedload(Employee.employee_clients).joinedload(EmployeeClient.client))\
        .get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return [ec.client for ec in emp.employee_clients]

@router.post("/", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    """ 직원 등록 (KST로 저장) """
    hashed_pw = get_password_hash(payload.password)
    new_emp = Employee(
        password_hash=hashed_pw,
        name=payload.name,
        phone=payload.phone,
        role=payload.role,
        birthday=payload.birthday,
        address=payload.address
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp  # ✅ 변환 없이 그대로 반환

@router.post("/login", response_model=EmployeeLoginResponse)
def login_employee(payload: EmployeeLogin, db: Session = Depends(get_db)):
    """ 직원 로그인 (JWT 발급) """
    emp = db.query(Employee).filter(Employee.id == payload.id).first()
    if not emp:
        raise HTTPException(status_code=401, detail="Invalid employee id.")
    if not verify_password(payload.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password.")

    token_data = {"sub": str(emp.id)}
    token = create_access_token(data=token_data)

    # ✅ UTF-8로 변환하여 반환
    return EmployeeLoginResponse(
        id=emp.id,
        name=emp.name.encode("utf-8").decode("utf-8"),  # ✅ 한글 깨짐 방지
        phone=emp.phone if emp.phone else None,  # ✅ phone 필드 유지
        role=emp.role,
        token=token
    )

@router.get("/", response_model=List[EmployeeOut])
def list_employees(name: str = Query(None, title="Employee Name"), db: Session = Depends(get_db)):
    """ 직원 목록 조회 (이름 검색 가능) """
    query = db.query(Employee)
    if name:
        query = query.filter(Employee.name.ilike(f"%{name}%"))
    return query.all()  # ✅ 변환 없이 그대로 반환

@router.get("/{emp_id}", response_model=EmployeeOut)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    """ 특정 직원 조회 (KST 변환 없음) """
    emp = db.query(Employee).get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp  # ✅ 변환 없이 그대로 반환

@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    """ 직원 삭제 (연결된 차량 정보도 함께 삭제) """
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="직원을 찾을 수 없습니다.")
    try:
        db.query(EmployeeVehicle).filter(EmployeeVehicle.employee_id == emp_id).delete()
        db.delete(emp)
        db.commit()
        return {"detail": "직원 및 관련 차량 정보 삭제 완료"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"직원 삭제 실패: {str(e)}")


@router.put("/{emp_id}", response_model=EmployeeOut)
def update_employee(emp_id: int, payload: EmployeeCreate, db: Session = Depends(get_db)):
    """
    emp_id: 정수형 PK (ex: 1,2,3...)
    """
    # 간단하게 get(pk)로 가져올 수 있음
    emp = db.query(Employee).get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # 비밀번호 변경 로직
    emp.password_hash = get_password_hash(payload.password)
    emp.name = payload.name
    emp.phone = payload.phone
    emp.role = payload.role
    emp.birthday = payload.birthday
    emp.address = payload.address

    db.commit()
    db.refresh(emp)
    return emp

@router.get("/me", response_model=EmployeeOut)
def get_current_employee(user: Employee = Depends(get_current_user)):
    """ 저장된 토큰 기반 현재 로그인한 직원 정보 반환 """
    return user