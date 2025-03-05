# app/routers/employee_map_routes.py
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
from app.utils.time_utils import convert_utc_to_kst, get_kst_today  # ✅ UTC → KST 변환 모듈 사용

router = APIRouter()

### ✅ 오늘 방문 기록 조회 (KST 적용) ###
@router.get("/employee_map/daily_visits")
def get_employee_daily_visits(
    employee_name: str = Query(..., description="검색할 직원 이름"),
    db: Session = Depends(get_db)
):
    """
    - 직원 이름(employee_name)으로 직원 찾기
    - '오늘(KST 기준)' 방문한 거래처 목록 조회
    - 거래처 주소를 기반으로 가짜 좌표(lat, lng) 생성
    - 당일 매출(today_sales) 계산하여 반환
    """

    # ✅ 직원 조회
    emp = db.query(Employee).filter(Employee.name == employee_name).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"직원 '{employee_name}'을 찾을 수 없습니다.")

    employee_id = emp.id
    kst_today = get_kst_today()  # ✅ 한국 시간 기준 오늘 날짜

    # ✅ 오늘 방문 기록 조회 (KST 적용)
    visits_q = (
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
        .filter(ClientVisit.employee_id == employee_id)
        .filter(cast(ClientVisit.visit_datetime, Date) == kst_today)  # ✅ KST 적용
        .group_by(
            ClientVisit.id,
            ClientVisit.visit_datetime,
            Client.id,
            Client.client_name,
            Client.address,
            Client.outstanding_amount
        )
        .order_by(ClientVisit.visit_datetime.asc())
    )

    rows = visits_q.all()
    if not rows:
        return []

    # ✅ 주소 → (lat, lng) 변환 함수 (실제 API로 교체 가능)
    def fake_address_to_coords(addr: str):
        import hashlib
        h = int(hashlib.md5(addr.encode("utf-8")).hexdigest(), 16)
        lat = 37.5 + (h % 10000) * 0.00001
        lng = 127.0 + (h % 10000) * 0.00001
        return lat, lng

    results = []
    for r in rows:
        lat, lng = fake_address_to_coords(r.address or "")
        visit_time_kst = convert_utc_to_kst(r.visit_datetime)  # ✅ KST 변환
        visit_time_str = visit_time_kst.strftime("%Y-%m-%d %H:%M:%S") if visit_time_kst else "N/A"

        results.append({
            "visit_id": r.visit_id,
            "visit_datetime": visit_time_str,  # ✅ KST 변환 후 반환
            "client_id": r.client_id,
            "client_name": r.client_name,
            "address": r.address,
            "lat": lat,
            "lng": lng,
            "outstanding_amount": float(r.outstanding_amount or 0),
            "today_sales": float(r.today_sales or 0),
        })

    return results


### ✅ 모든 방문 기록 조회 (날짜 제한 없음, KST 적용) ###
@router.get("/employee_map/all_visits")
def get_all_employee_visits(
    employee_name: str = Query(..., description="검색할 직원 이름"),
    db: Session = Depends(get_db)
):
    """
    - 직원 이름으로 직원 조회
    - 해당 직원이 방문한 모든 거래처 조회 (날짜 관계없음)
    - 거래처 주소(Client.address)를 기반으로 가짜 좌표(lat, lng) 생성
    - 당일 매출(today_sales) 계산하여 반환
    """

    # ✅ 직원 조회
    emp = db.query(Employee).filter(Employee.name == employee_name).first()
    if not emp:
        raise HTTPException(status_code=404, detail=f"직원 '{employee_name}'을 찾을 수 없습니다.")

    employee_id = emp.id

    # ✅ 날짜 조건 없이 모든 방문 기록 조회
    visits_q = (
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
            (SalesRecord.employee_id == ClientVisit.employee_id)
        )
        .outerjoin(Product, Product.id == SalesRecord.product_id)
        .filter(ClientVisit.employee_id == employee_id)
        .group_by(
            ClientVisit.id,
            ClientVisit.visit_datetime,
            Client.id,
            Client.client_name,
            Client.address,
            Client.outstanding_amount
        )
        .order_by(ClientVisit.visit_datetime.asc())
    )

    rows = visits_q.all()
    if not rows:
        return []

    # ✅ 클라이언트 주소를 기반으로 가짜 좌표 생성
    def fake_address_to_coords(addr: str):
        import hashlib
        h = int(hashlib.md5(addr.encode("utf-8")).hexdigest(), 16)
        lat = 37.5 + (h % 10000) * 0.00001
        lng = 127.0 + (h % 10000) * 0.00001
        return lat, lng
    
    from datetime import timezone

    UTC = timezone.utc  # ✅ UTC 정의

    
    def is_utc(dt):
        return dt.tzinfo is None or dt.tzinfo == UTC  # ✅ UTC인지 확인

    results = []
    for r in rows:
        lat, lng = fake_address_to_coords(r.address or "")
        # ✅ visit_datetime이 UTC인지 확인 후 변환 (중복 변환 방지)
        if is_utc(r.visit_datetime):
            visit_time_kst = r.visit_datetime  # ✅ UTC일 경우 변환
        else:
            visit_time_kst = r.visit_datetime  # ✅ 이미 KST라면 그대로 사용
        visit_time_str = visit_time_kst.strftime("%Y-%m-%d %H:%M:%S") if visit_time_kst else "N/A"

        results.append({
            "visit_id": r.visit_id,
            "visit_datetime": visit_time_str,  # ✅ KST 변환 후 반환
            "client_id": r.client_id,
            "client_name": r.client_name,
            "address": r.address,
            "lat": lat,
            "lng": lng,
            "outstanding_amount": float(r.outstanding_amount or 0),
            "today_sales": float(r.today_sales or 0),
        })

    return results
