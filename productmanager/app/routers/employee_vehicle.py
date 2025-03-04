from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.employee_vehicle import EmployeeVehicle
from app.schemas.employee_vehicle import EmployeeVehicleCreate, EmployeeVehicleOut
from app.utils.time_utils import convert_utc_to_kst  # ✅ UTC → KST 변환 함수 추가

router = APIRouter()

@router.post("/", response_model=EmployeeVehicleOut)
def create_employee_vehicle(vehicle_data: EmployeeVehicleCreate, db: Session = Depends(get_db)):
    """ 차량 정보 등록 (KST 변환 적용) """
    try:
        new_vehicle = EmployeeVehicle(**vehicle_data.dict())  
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        # ✅ `datetime`을 `str`로 변환하여 반환 (KST 변환 적용)
        return convert_employee_vehicle_to_kst(new_vehicle)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"차량 등록 오류: {str(e)}")

@router.get("/", response_model=list[EmployeeVehicleOut])
def list_employee_vehicles(db: Session = Depends(get_db)):
    """
    모든 직원 차량 정보 조회 (KST 변환 적용)
    """
    vehicles = db.query(EmployeeVehicle).all()
    return [convert_employee_vehicle_to_kst(v) for v in vehicles]  # ✅ KST 변환 적용

@router.get("/{emp_id}", response_model=EmployeeVehicleOut)
def get_employee_vehicle(emp_id: int, db: Session = Depends(get_db)):
    """ 특정 직원의 차량 정보 조회 (KST 변환 적용) """
    vehicle = db.query(EmployeeVehicle).filter(EmployeeVehicle.employee_id == emp_id).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="차량 정보가 존재하지 않습니다.")

    return convert_employee_vehicle_to_kst(vehicle)  # ✅ KST 변환 적용

def convert_employee_vehicle_to_kst(vehicle: EmployeeVehicle):
    """
    EmployeeVehicle 객체의 날짜/시간 필드를 KST로 변환하여 반환
    """
    return {
        "id": vehicle.id,
        "employee_id": vehicle.employee_id,
        "monthly_fuel_cost": vehicle.monthly_fuel_cost,
        "current_mileage": vehicle.current_mileage,
        "last_engine_oil_change": convert_utc_to_kst(vehicle.last_engine_oil_change).strftime("%Y-%m-%d") if vehicle.last_engine_oil_change else None,
        "created_at": convert_utc_to_kst(vehicle.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": convert_utc_to_kst(vehicle.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
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
