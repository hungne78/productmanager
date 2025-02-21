from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_vehicle import EmployeeVehicle
from app.schemas.employee_vehicle import EmployeeVehicleCreate, EmployeeVehicleOut

router = APIRouter()

@router.post("/", response_model=EmployeeVehicleOut)
def create_employee_vehicle(payload: EmployeeVehicleCreate, db: Session = Depends(get_db)):
    # 중복 등록 방지: 해당 직원의 차량 관리 정보가 이미 있으면 오류 처리
    existing = db.query(EmployeeVehicle).filter(EmployeeVehicle.employee_id == payload.employee_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee vehicle record already exists.")
    new_vehicle = EmployeeVehicle(
        employee_id=payload.id,
        monthly_fuel_cost=payload.monthly_fuel_cost,
        current_mileage=payload.current_mileage,
        last_engine_oil_change=payload.last_engine_oil_change
    )
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    result = new_vehicle.__dict__.copy()
    result["id_employee"] = result.pop("employee_id")
    return result

@router.get("/", response_model=list[EmployeeVehicleOut])
def list_employee_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(EmployeeVehicle).all()
    return vehicles

@router.get("/{vehicle_id}", response_model=EmployeeVehicleOut)
def get_employee_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(EmployeeVehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Employee vehicle record not found")
    result = vehicle.__dict__.copy()
    result["id_employee"] = result.pop("employee_id")
    return result

@router.put("/{vehicle_id}", response_model=EmployeeVehicleOut)
def update_employee_vehicle(vehicle_id: int, payload: EmployeeVehicleCreate, db: Session = Depends(get_db)):
    vehicle = db.query(EmployeeVehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Employee vehicle record not found")
    vehicle.monthly_fuel_cost = payload.monthly_fuel_cost
    vehicle.current_mileage = payload.current_mileage
    vehicle.last_engine_oil_change = payload.last_engine_oil_change
    db.commit()
    db.refresh(vehicle)
    result = vehicle.__dict__.copy()
    result["id_employee"] = result.pop("employee_id")
    return result

@router.delete("/{vehicle_id}")
def delete_employee_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(EmployeeVehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Employee vehicle record not found")
    db.delete(vehicle)
    db.commit()
    return {"detail": "Employee vehicle record deleted"}
