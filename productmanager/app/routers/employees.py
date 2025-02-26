# app/routers/employees.py
from fastapi import APIRouter, Depends, HTTPException,  Query
from sqlalchemy.orm import Session
from app.db.database import get_db
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
from sqlalchemy.orm import Session, joinedload
from typing import List
router = APIRouter()

@router.get("/{emp_id}/clients", response_model=List[ClientOut])
def get_employee_clients(emp_id: int, db: Session = Depends(get_db)):
    """
    특정 사원이 담당하는 거래처 목록 조회
    """
    emp = db.query(Employee)\
        .options(joinedload(Employee.employee_clients).joinedload(EmployeeClient.client))\
        .get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # emp.employee_clients는 List[EmployeeClient]
    # 각 EmployeeClient 객체에 .client가 있음
    # → Client 객체들이므로, ClientOut 스키마로 변환
    return [ec.client for ec in emp.employee_clients]

@router.post("/", response_model=EmployeeOut)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # 중복 체크
    # existing = db.query(Employee).filter(Employee.employee_number == payload.employee_number).first()
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Employee number already in use."
    #     )
    # 비번 해시
    hashed_pw = get_password_hash(payload.password)
    new_emp = Employee(
        # employee_number=payload.employee_number,
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
    return new_emp

@router.post("/login", response_model=EmployeeLoginResponse)
def login_employee(payload: EmployeeLogin, db: Session = Depends(get_db)):
    """
    - 'employee_number' 없이, 'id'와 'password'로만 로그인
    - 토큰 생성 시 'sub'에 emp.id (또는 str(emp.id))를 넣음
    - 로그인 성공 시 EmployeeLoginResponse를 반환
    """
    # 1) id로 직원 조회
    emp = db.query(Employee).filter(Employee.id == payload.id).first()
    if not emp:
        raise HTTPException(status_code=401, detail="Invalid employee id.")

    # 2) 비번 검증
    if not verify_password(payload.password, emp.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password.")

    # 3) JWT 토큰 생성
    #    'sub'에 직원 식별자를 넣을 수 있음 (여기서는 emp.id 사용)
    token_data = {"sub": str(emp.id)}
    token = create_access_token(data=token_data)

    # 4) 응답 스키마로 변환
    return EmployeeLoginResponse(
        id=emp.id,
        name=emp.name,
        phone=emp.phone,
        role=emp.role,
        token=token
    )

@router.get("/", response_model=List[EmployeeOut])
def list_employees(name: str = Query(None, title="Employee Name"), db: Session = Depends(get_db)):
    """
    직원 목록 조회 (이름 검색 기능 포함)
    """
    query = db.query(Employee)
    if name:
        query = query.filter(Employee.name.ilike(f"%{name}%"))  # 부분 검색 지원
    employees = query.all()
    
    return employees

@router.get("/{emp_id}", response_model=EmployeeOut)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).get(emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"detail": "Employee deleted"}

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

