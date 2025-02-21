from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_vehicle import EmployeeVehicle
from app.schemas.employee_vehicle import EmployeeVehicleCreate, EmployeeVehicleOut
import json  # 로그 출력용

router = APIRouter()

@router.post("", response_model=EmployeeVehicleOut)
def create_employee_vehicle(payload: EmployeeVehicleCreate, db: Session = Depends(get_db)):
    print("🔍 서버에서 받은 데이터:", payload.dict(), flush=True)
    print("📌 last_engine_oil_change 타입:", type(payload.last_engine_oil_change))

    existing = db.query(EmployeeVehicle).filter(EmployeeVehicle.id == payload.id).first()
    
    if existing:
        print(f"⚠️ 기존 차량 기록 삭제: ID {payload.id}")
        db.delete(existing)
        db.commit()  # ✅ 기존 데이터 삭제 후 커밋

    # 새로운 차량 정보 추가
    new_vehicle = EmployeeVehicle(
        id=payload.id,
        monthly_fuel_cost=payload.monthly_fuel_cost,
        current_mileage=payload.current_mileage,
        last_engine_oil_change=payload.last_engine_oil_change
    )

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return EmployeeVehicleOut.from_orm(new_vehicle)





@router.get("", response_model=list[EmployeeVehicleOut])
def list_employee_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(EmployeeVehicle).all()
    
    # ✅ date와 datetime을 문자열로 변환
    response_data = []
    for v in vehicles:
        response_data.append({
            "id": v.id,
            "monthly_fuel_cost": v.monthly_fuel_cost,
            "current_mileage": v.current_mileage,
            "last_engine_oil_change": v.last_engine_oil_change.strftime("%Y-%m-%d") if v.last_engine_oil_change else None,
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": v.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return response_data  # ✅ FastAPI가 JSON 변환 가능하도록 수정



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
