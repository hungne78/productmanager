from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employees import Employee
from app.schemas.employees import EmployeeLogin, EmployeeLoginResponse
from app.core.security import verify_password, create_access_token

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
