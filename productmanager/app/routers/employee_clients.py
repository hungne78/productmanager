# app/routers/employee_clients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.employee_clients import EmployeeClient
from app.schemas.employee_clients import EmployeeClientCreate, EmployeeClientOut
from pydantic import BaseModel
from datetime import date
from app.utils.time_utils import get_kst_today, convert_utc_to_kst  # ✅ KST 변환 함수 추가

router = APIRouter()
class EmployeeUnassignRequest(BaseModel):
    client_id: int
    employee_id: int

@router.post("/", response_model=EmployeeClientOut)
def assign_employee_client(payload: EmployeeClientCreate, db: Session = Depends(get_db)):
    """ 사원과 거래처를 연결(전담 배정)하는 엔드포인트 (KST로 저장) """
    existing = db.query(EmployeeClient).filter(
        EmployeeClient.employee_id == payload.employee_id,
        EmployeeClient.client_id == payload.client_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee-Client relation already exists.")

    new_ec = EmployeeClient(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        start_date=payload.start_date if payload.start_date else get_kst_today(),
        end_date=payload.end_date if payload.end_date else get_kst_today()
    )
    db.add(new_ec)
    db.commit()
    db.refresh(new_ec)
    return new_ec  # ✅ 변환 없이 그대로 반환


@router.get("/", response_model=List[EmployeeClientOut])
def list_employee_clients(db: Session = Depends(get_db)):
    """ 모든 employee-client 전담 관계 조회 (KST 그대로 반환) """
    return db.query(EmployeeClient).all()  # ✅ 변환 없이 그대로 반환

@router.get("/{ec_id}", response_model=EmployeeClientOut)
def get_employee_client(ec_id: int, db: Session = Depends(get_db)):
    """ 특정 employee-client 관계 조회 (KST 변환 없음) """
    ec = db.query(EmployeeClient).get(ec_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Employee-Client relation not found")
    return ec  # ✅ 변환 없이 그대로 반환

@router.delete("/{ec_id}")
def delete_employee_client(ec_id: int, db: Session = Depends(get_db)):
    """ 특정 employee-client 관계 삭제 """
    ec = db.query(EmployeeClient).get(ec_id)
    if not ec:
        raise HTTPException(status_code=404, detail="Employee-Client relation not found")
    db.delete(ec)
    db.commit()
    return {"detail": "Employee-Client relation deleted"}

@router.post("/unassign")
def unassign_employee(data: EmployeeUnassignRequest, db: Session = Depends(get_db)):
    """ 특정 직원과 거래처의 관계 해제 """
    employee_client = db.query(EmployeeClient).filter(
        EmployeeClient.client_id == data.client_id,
        EmployeeClient.employee_id == data.employee_id
    ).first()

    if not employee_client:
        raise HTTPException(status_code=404, detail="해당 직원과 거래처의 연결을 찾을 수 없습니다.")

    try:
        db.delete(employee_client)
        db.commit()
        return {"message": "담당 직원 해제가 완료되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"담당 직원 해제 실패: {str(e)}")