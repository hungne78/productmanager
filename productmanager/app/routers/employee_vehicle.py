from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_vehicle import EmployeeVehicle
from app.schemas.employee_vehicle import EmployeeVehicleCreate, EmployeeVehicleOut
import json  # 로그 출력용

router = APIRouter()

@router.post("/", response_model=EmployeeVehicleOut)  # ✅ 응답은 EmployeeVehicleOut 유지
def create_employee_vehicle(vehicle_data: EmployeeVehicleCreate, db: Session = Depends(get_db)):
    """ 차량 정보 등록 """
    try:
        new_vehicle = EmployeeVehicle(**vehicle_data.dict())  # ✅ `id` 없이 생성
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        # ✅ `datetime`을 `str`로 변환하여 반환
        return {
            "id": new_vehicle.id,
            "employee_id": new_vehicle.employee_id,
            "monthly_fuel_cost": new_vehicle.monthly_fuel_cost,
            "current_mileage": new_vehicle.current_mileage,
            "last_engine_oil_change": new_vehicle.last_engine_oil_change.strftime("%Y-%m-%d") if new_vehicle.last_engine_oil_change else None,
            "created_at": new_vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": new_vehicle.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"차량 등록 오류: {str(e)}")



@router.get("/", response_model=list[EmployeeVehicleOut])
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



@router.get("/{emp_id}", response_model=EmployeeVehicleOut)
def get_employee_vehicle(emp_id: int, db: Session = Depends(get_db)):
    """ 특정 직원의 차량 정보 조회 """
    print(f"🚀 차량 정보 조회 요청: 직원 ID = {emp_id}")
    vehicle = db.query(EmployeeVehicle).filter(EmployeeVehicle.employee_id == emp_id).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="차량 정보가 존재하지 않습니다.")

    # ✅ `datetime`을 `str`로 변환
    return {
        "id": vehicle.id,
        "monthly_fuel_cost": vehicle.monthly_fuel_cost,
        "current_mileage": vehicle.current_mileage,
        "last_engine_oil_change": vehicle.last_engine_oil_change.strftime("%Y-%m-%d") if vehicle.last_engine_oil_change else None,
        "created_at": vehicle.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": vehicle.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    }

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
