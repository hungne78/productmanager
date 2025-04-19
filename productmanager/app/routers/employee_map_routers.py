from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime
from app.db.database import get_db
from app.models.employees import Employee
from app.models.client_visits import ClientVisit
from app.models.clients import Client
from app.models.sales_records import SalesRecord
from app.models.products import Product
from app.utils.time_utils import convert_utc_to_kst, get_kst_today  # ✅ 시간 유틸

router = APIRouter()


def fake_address_to_coords(addr: str):
    import hashlib
    h = int(hashlib.md5(addr.encode("utf-8")).hexdigest(), 16)
    lat = 37.5 + (h % 10000) * 0.00001
    lng = 127.0 + (h % 10000) * 0.00001
    return lat, lng


### ✅ 1. 오늘 방문 기록 조회 (직원 이름으로)
@router.get("/employee_map/daily_visits")
def get_employee_daily_visits(
    employee_name: str = Query(..., description="직원 이름"),
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.name == employee_name).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"직원 '{employee_name}'을 찾을 수 없습니다.")

    kst_today = get_kst_today()

    rows = (
        db.query(
            ClientVisit.id.label("visit_id"),
            ClientVisit.visit_datetime,
            Client.id.label("client_id"),
            Client.client_name,
            Client.address,
            Client.outstanding_amount,
            func.coalesce(
                func.sum(Product.default_price * SalesRecord.quantity), 0
            ).label("today_sales")
        )
        .join(Client, ClientVisit.client_id == Client.id)
        .outerjoin(
            SalesRecord,
            (SalesRecord.client_id == ClientVisit.client_id) &
            (SalesRecord.employee_id == ClientVisit.employee_id) &
            (cast(SalesRecord.sale_datetime, Date) == cast(ClientVisit.visit_datetime, Date))
        )
        .outerjoin(Product, Product.id == SalesRecord.product_id)
        .filter(ClientVisit.employee_id == emp.id)
        .filter(cast(ClientVisit.visit_datetime, Date) == kst_today)
        .group_by(
            ClientVisit.id,
            ClientVisit.visit_datetime,
            Client.id,
            Client.client_name,
            Client.address,
            Client.outstanding_amount
        )
        .order_by(ClientVisit.visit_datetime.asc())
        .all()
    )

    return [
        {
            "visit_id": r.visit_id,
            "visit_datetime": convert_utc_to_kst(r.visit_datetime).strftime("%Y-%m-%d %H:%M:%S"),
            "client_id": r.client_id,
            "client_name": r.client_name,
            "address": r.address,
            "lat": fake_address_to_coords(r.address or "")[0],
            "lon": fake_address_to_coords(r.address or "")[1],
            "outstanding_amount": float(r.outstanding_amount or 0),
            "today_sales": float(r.today_sales or 0),
            "employee_id": emp.id,
            "employee_name": emp.name,
        }
        for r in rows
    ]


### ✅ 2. 전체 직원들의 오늘 방문 기록 (지도 초기용)
@router.get("/employee_map/daily_visits/init")
def get_all_today_visits(db: Session = Depends(get_db)):
    """
    전체 직원들의 오늘 방문 기록을 초기 로딩용으로 반환
    """
    kst_today = get_kst_today()

    visits = (
        db.query(
            Employee.id.label("employee_id"),
            Employee.name.label("employee_name"),
            ClientVisit.id.label("visit_id"),
            ClientVisit.visit_datetime,
            Client.id.label("client_id"),
            Client.client_name,
            Client.address,
            Client.outstanding_amount,
            func.coalesce(
                func.sum(Product.default_price * SalesRecord.quantity), 0
            ).label("today_sales")
        )
        .join(ClientVisit, ClientVisit.employee_id == Employee.id)
        .join(Client, ClientVisit.client_id == Client.id)
        .outerjoin(
            SalesRecord,
            (SalesRecord.client_id == ClientVisit.client_id) &
            (SalesRecord.employee_id == ClientVisit.employee_id) &
            (cast(SalesRecord.sale_datetime, Date) == cast(ClientVisit.visit_datetime, Date))
        )
        .outerjoin(Product, Product.id == SalesRecord.product_id)
        .filter(cast(ClientVisit.visit_datetime, Date) == kst_today)
        .group_by(
            Employee.id,
            Employee.name,
            ClientVisit.id,
            ClientVisit.visit_datetime,
            Client.id,
            Client.client_name,
            Client.address,
            Client.outstanding_amount
        )
        .order_by(Employee.name.asc(), ClientVisit.visit_datetime.asc())
        .all()
    )

    results = []
    for r in visits:
        lat, lon = fake_address_to_coords(r.address or "")
        results.append({
            "visit_id": r.visit_id,
            "visit_datetime": convert_utc_to_kst(r.visit_datetime).strftime("%Y-%m-%d %H:%M:%S"),
            "client_id": r.client_id,
            "client_name": r.client_name,
            "address": r.address,
            "lat": lat,
            "lon": lon,
            "outstanding_amount": float(r.outstanding_amount or 0),
            "today_sales": float(r.today_sales or 0),
            "employee_id": r.employee_id,
            "employee_name": r.employee_name,
        })

    return results
