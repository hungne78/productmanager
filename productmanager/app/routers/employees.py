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
from datetime import datetime
from app.utils.sales_table_utils import get_sales_model
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

@router.get("/basic_info", response_model=List[dict])
def get_employees_basic_info(db: Session = Depends(get_db)):
    """직원 기본 정보 목록 반환 (Flutter 리스트 화면용)"""
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord
    from app.models.clients import Client
    from app.models.products import Product
    today = datetime.now().date()

    employees = db.query(Employee).all()
    result = []

    for emp in employees:
        today_sales = (
            db.query(func.sum(Product.default_price * SalesRecord.quantity))
            .select_from(SalesRecord)  # 💡 기준 테이블 명시
            .join(Product, Product.id == SalesRecord.product_id)  # 💡 ON 조건 명시
            .filter(SalesRecord.employee_id == emp.id)
            .filter(func.date(SalesRecord.sale_datetime) == today)
            .scalar()
        )

        today_orders = (
            db.query(SalesRecord)
            .filter(SalesRecord.employee_id == emp.id)
            .filter(func.date(SalesRecord.sale_datetime) == today)
            .count()
        )

        total_outstanding = (
            db.query(func.sum(Client.outstanding_amount))
            .join(EmployeeClient, EmployeeClient.client_id == Client.id)
            .filter(EmployeeClient.employee_id == emp.id)
            .scalar()
        ) or 0

        result.append({
            "employee_id": emp.id,
            "name": emp.name,
            "today_sales": int(today_sales or 0),
            "today_order_count": today_orders,
            "total_outstanding": int(total_outstanding or 0),
        })
    return result


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

@router.get("/admin/employees/{employee_id}/profile")
def get_employee_profile(employee_id: int, db: Session = Depends(get_db)):
    from app.models.employees import Employee
    from app.models.employee_vehicle import EmployeeVehicle
    from app.models.employee_clients import EmployeeClient
    from app.models.clients import Client

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="해당 직원을 찾을 수 없습니다.")

    # 차량 재고
    vehicle = db.query(EmployeeVehicle).filter(EmployeeVehicle.employee_id == employee_id).first()
    vehicle_info = {
        "monthly_fuel_cost": vehicle.monthly_fuel_cost if vehicle else 0,
        "current_mileage": vehicle.current_mileage if vehicle else 0,
        "last_engine_oil_change": str(vehicle.last_engine_oil_change) if vehicle and vehicle.last_engine_oil_change else None
    }

    # 담당 거래처
    client_links = db.query(EmployeeClient).filter(EmployeeClient.employee_id == employee_id).all()
    client_list = []
    for link in client_links:
        client = db.query(Client).filter(Client.id == link.client_id).first()
        if client:
            client_list.append({
                "client_id": client.id,
                "client_name": client.client_name,
                "address": client.address,
                "outstanding": client.outstanding_amount,
            })

    return {
        "id": emp.id,
        "name": emp.name,
        "phone": emp.phone,
        "birthday": str(emp.birthday) if emp.birthday else None,
        "address": emp.address,
        "role": emp.role,
        "vehicle": vehicle_info,
        "clients": client_list,
    }
    
@router.get("/admin/employees/{employee_id}/stats/daily")
def get_employee_daily_stats(employee_id: int, db: Session = Depends(get_db)):
    from app.utils.sales_utils import get_sales_model
    from app.models.products import Product
    from sqlalchemy import func

    today = datetime.now().date()
    SalesRecord = get_sales_model(today.year)

    sales_sum = (
        db.query(func.sum(Product.default_price * SalesRecord.quantity))
        .select_from(SalesRecord)
        .join(Product, Product.id == SalesRecord.product_id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(func.date(SalesRecord.sale_datetime) == today)
        .scalar()
    ) or 0

    order_count = db.query(SalesRecord).filter(
        SalesRecord.employee_id == employee_id,
        func.date(SalesRecord.sale_datetime) == today
    ).count()

    client_visits = db.query(SalesRecord.client_id).filter(
        SalesRecord.employee_id == employee_id,
        func.date(SalesRecord.sale_datetime) == today
    ).distinct().count()

    return {
        "sales": int(sales_sum),
        "orders": order_count,
        "visits": client_visits,
    }

@router.get("/admin/employees/{employee_id}/stats/monthly")
def get_employee_monthly_stats(employee_id: int, db: Session = Depends(get_db)):
    from app.models.sales_records import SalesRecord
    from app.models.products import Product
    from sqlalchemy import func
    today = datetime.now().date()
    SalesRecord = get_sales_model(today.year)
    now = datetime.now()
    first_day = datetime(now.year, now.month, 1)
    last_moment_today = datetime.combine(now.date(), datetime.max.time())  # 23:59:59.999999

    sales_sum = (
        db.query(func.sum(Product.default_price * SalesRecord.quantity))
        .select_from(SalesRecord)
        .join(Product, Product.id == SalesRecord.product_id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(SalesRecord.sale_datetime >= first_day)
        .filter(SalesRecord.sale_datetime <= last_moment_today)
        .scalar()
    ) or 0


    order_count = db.query(SalesRecord).filter(
        SalesRecord.employee_id == employee_id,
        SalesRecord.sale_datetime >= first_day,
        SalesRecord.sale_datetime <= now
    ).count()

    visit_count = db.query(SalesRecord.client_id).filter(
        SalesRecord.employee_id == employee_id,
        SalesRecord.sale_datetime >= first_day,
        SalesRecord.sale_datetime <= now
    ).distinct().count()

    return {
        "sales": int(sales_sum),
        "orders": order_count,
        "visits": visit_count
    }

@router.get("/admin/employees/{employee_id}/stats/yearly")
def get_employee_yearly_stats(employee_id: int, db: Session = Depends(get_db)):
    from app.models.sales_records import SalesRecord
    from app.models.products import Product
    from sqlalchemy import func
    today = datetime.now().date()
    SalesRecord = get_sales_model(today.year)
    now = datetime.now()
    first_day_of_year = datetime(now.year, 1, 1)
    end_of_today = datetime.combine(now.date(), datetime.max.time())

    sales_sum = (
        db.query(func.sum(Product.default_price * SalesRecord.quantity))
        .select_from(SalesRecord)
        .join(Product, Product.id == SalesRecord.product_id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(SalesRecord.sale_datetime >= first_day_of_year)
        .filter(SalesRecord.sale_datetime <= end_of_today)
        .scalar()
    ) or 0

    order_count = db.query(SalesRecord).filter(
        SalesRecord.employee_id == employee_id,
        SalesRecord.sale_datetime >= first_day_of_year,
        SalesRecord.sale_datetime <= end_of_today
    ).count()

    client_visits = db.query(SalesRecord.client_id).filter(
        SalesRecord.employee_id == employee_id,
        SalesRecord.sale_datetime >= first_day_of_year,
        SalesRecord.sale_datetime <= end_of_today
    ).distinct().count()

    return {
        "sales": int(sales_sum),
        "orders": order_count,
        "visits": client_visits,
    }

@router.get("/admin/employees/{employee_id}/clients/stats")
def get_employee_client_stats(employee_id: int, db: Session = Depends(get_db)):
    from app.models.clients import Client
    from app.models.sales_records import SalesRecord
    from app.models.employee_clients import EmployeeClient
    from app.models.products import Product
    from sqlalchemy import func
    today = datetime.now().date()
    SalesRecord = get_sales_model(today.year)
    now = datetime.now()
    
    end_of_today = datetime.combine(today, datetime.max.time())  # 오늘의 23:59:59.999999
    first_day_of_month = datetime(now.year, now.month, 1)
    first_day_of_year = datetime(now.year, 1, 1)

    links = db.query(EmployeeClient).filter(EmployeeClient.employee_id == employee_id).all()

    result = []
    for link in links:
        client = db.query(Client).filter(Client.id == link.client_id).first()
        if not client:
            continue

        # 🔸 일매출
        daily_sales = (
            db.query(func.sum(Product.default_price * SalesRecord.quantity))
            .select_from(SalesRecord)
            .join(Product, Product.id == SalesRecord.product_id)
            .filter(SalesRecord.employee_id == employee_id)
            .filter(SalesRecord.client_id == client.id)
            .filter(func.date(SalesRecord.sale_datetime) == today)
            .scalar()
        ) or 0

        # 🔸 월매출 (오늘 포함)
        monthly_sales = (
            db.query(func.sum(Product.default_price * SalesRecord.quantity))
            .select_from(SalesRecord)
            .join(Product, Product.id == SalesRecord.product_id)
            .filter(SalesRecord.employee_id == employee_id)
            .filter(SalesRecord.client_id == client.id)
            .filter(SalesRecord.sale_datetime >= first_day_of_month)
            .filter(SalesRecord.sale_datetime <= end_of_today)
            .scalar()
        ) or 0

        # 🔸 연매출 (오늘 포함)
        yearly_sales = (
            db.query(func.sum(Product.default_price * SalesRecord.quantity))
            .select_from(SalesRecord)
            .join(Product, Product.id == SalesRecord.product_id)
            .filter(SalesRecord.employee_id == employee_id)
            .filter(SalesRecord.client_id == client.id)
            .filter(SalesRecord.sale_datetime >= first_day_of_year)
            .filter(SalesRecord.sale_datetime <= end_of_today)
            .scalar()
        ) or 0

        # 🔸 방문 수 (월 기준, 오늘 포함)
        monthly_visits = db.query(SalesRecord.client_id).filter(
            SalesRecord.employee_id == employee_id,
            SalesRecord.client_id == client.id,
            SalesRecord.sale_datetime >= first_day_of_month,
            SalesRecord.sale_datetime <= end_of_today
        ).distinct().count()

        result.append({
            "client_id": client.id,
            "client_name": client.client_name,
            "daily_sales": int(daily_sales),
            "monthly_sales": int(monthly_sales),
            "yearly_sales": int(yearly_sales),
            "outstanding": int(client.outstanding_amount or 0),
            "monthly_visits": monthly_visits,
        })

    return result
