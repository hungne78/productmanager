# app/routers/employee_clients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.employee_clients import EmployeeClient
from app.schemas.employee_clients import EmployeeClientCreate, EmployeeClientOut

router = APIRouter()

@router.post("/", response_model=EmployeeClientOut)
def assign_employee_client(payload: EmployeeClientCreate, db: Session = Depends(get_db)):
    """
    사원과 거래처를 연결(전담 배정)하는 엔드포인트
    """
    # 중복 체크(같은 employee_id + client_id가 이미 있는지)
    existing = db.query(EmployeeClient).filter(
        EmployeeClient.employee_id == payload.employee_id,
        EmployeeClient.client_id == payload.client_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee-Client relation already exists.")

    new_ec = EmployeeClient(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    db.add(new_ec)
    db.commit()
    db.refresh(new_ec)
    return new_ec

@router.get("/", response_model=List[EmployeeClientOut])
def list_employee_clients(db: Session = Depends(get_db)):
    """
    모든 employee-client 전담 관계 조회
    """
    return db.query(EmployeeClient).all()

@router.get("/{ec_id}", response_model=EmployeeClientOut)
def get_employee_client(ec_id: int, db: Session = Depends(get_db)):
    ec = db.query(EmployeeClient).get(ec_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Employee-Client relation not found")
    return ec

@router.delete("/{ec_id}")
def delete_employee_client(ec_id: int, db: Session = Depends(get_db)):
    ec = db.query(EmployeeClient).get(ec_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Employee-Client relation not found")
    db.delete(ec)
    db.commit()
    return {"detail": "Employee-Client relation deleted"}
