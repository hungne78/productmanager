from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client_visits import ClientVisit
from app.models.clients import Client
from typing import List
from app.schemas.client_visits import ClientVisitCreate, ClientVisitOut
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta, timezone
from app.models.sales_records import SalesRecord
from app.models.products import Product
# ✅ extract 함수 임포트 추가
from sqlalchemy import extract, func
from app.utils.time_utils import convert_utc_to_kst, get_kst_today, get_kst_now  # ✅ UTC → KST 변환 함수 추가
from app.utils.visit_table_utils import get_visit_model # ✅ 연도에 맞는 테이블 모델 가져오기
from app.utils.sales_table_utils import get_sales_model # ✅ 연도에 맞는 테이블 모델 가져오기
router = APIRouter()

@router.post("/", response_model=ClientVisitOut)
def create_client_visit(payload: ClientVisitCreate, db: Session = Depends(get_db)):
    year = payload.visit_datetime.date().year
    VisitModel = get_visit_model(year)

    new_visit = VisitModel(
        employee_id=payload.id,
        client_id=payload.client_id,
        visit_datetime=payload.visit_datetime,
        visit_date=payload.visit_datetime.date(),
        order_id=payload.order_id
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    return new_visit

@router.get("/", response_model=List[ClientVisitOut])
def list_client_visits(year: int = Query(datetime.now().year), db: Session = Depends(get_db)):
    VisitModel = get_visit_model(year)
    visits = db.query(VisitModel).all()
    return visits



@router.get("/monthly_visits/{employee_id}/{year}")
def get_monthly_visits(employee_id: int, year: int, db: Session = Depends(get_db)):
    VisitModel = get_visit_model(year)

    results = (
        db.query(
            extract('month', VisitModel.visit_datetime).label('visit_month'),
            func.count(VisitModel.id).label('cnt')
        )
        .filter(VisitModel.employee_id == employee_id)
        .group_by("visit_month")
        .all()
    )

    monthly_counts = [0] * 12
    for row in results:
        monthly_counts[int(row.visit_month) - 1] = row.cnt

    return monthly_counts


@router.get("/daily_visits/{employee_id}/{year}/{month}")
def get_daily_visits(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    VisitModel = get_visit_model(year)

    daily_counts = [0] * 31
    results = (
        db.query(
            extract('day', VisitModel.visit_datetime).label('visit_day'),
            func.count(VisitModel.id).label('cnt')
        )
        .filter(VisitModel.employee_id == employee_id)
        .filter(extract('month', VisitModel.visit_datetime) == month)
        .group_by("visit_day")
        .all()
    )

    for r in results:
        daily_counts[int(r.visit_day) - 1] = r.cnt

    return daily_counts

def get_kst_today():
    """현재 날짜를 KST(Asia/Seoul) 기준으로 변환"""
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9))).date()



@router.get("/today_visits_details")
def get_today_visits_details(employee_id: int = Query(...), db: Session = Depends(get_db)):
    today_kst = get_kst_today()
    VisitModel = get_visit_model(today_kst.year)
    SalesModel = get_sales_model(today_kst.year)  # ✅ 매출 테이블도 연도에 맞게 분기

    query = (
        db.query(
            VisitModel.id.label("visit_id"),
            VisitModel.visit_datetime,
            VisitModel.visit_count,
            Client.id.label("client_id"),
            Client.client_name,
            Client.outstanding_amount,
            func.coalesce(func.sum(SalesModel.total_amount), 0).label("today_sales")
        )
        .join(Client, VisitModel.client_id == Client.id)
        .outerjoin(
            SalesModel,
            (SalesModel.client_id == VisitModel.client_id) &
            (SalesModel.employee_id == VisitModel.employee_id) &
            (cast(SalesModel.sale_datetime, Date) == cast(VisitModel.visit_datetime, Date))
        )
        .filter(VisitModel.employee_id == employee_id)
        .filter(VisitModel.visit_date == today_kst)
        .group_by(
            VisitModel.id, VisitModel.visit_datetime, VisitModel.visit_count,
            Client.id, Client.client_name, Client.outstanding_amount
        )
        .all()
    )

    results = []
    for row in query:
        results.append({
            "visit_id": row.visit_id,
            "visit_datetime": row.visit_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "visit_count": row.visit_count,
            "client_id": row.client_id,
            "client_name": row.client_name,
            "outstanding_amount": float(row.outstanding_amount or 0),
            "today_sales": float(row.today_sales or 0),
        })

    return results



@router.get("/monthly_visits_client/{client_id}/{year}")
def get_monthly_visits_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    VisitModel = get_visit_model(year)

    monthly_visits = [0] * 12
    visits = (
        db.query(extract("month", VisitModel.visit_datetime), func.count())
        .filter(VisitModel.client_id == client_id)
        .group_by(extract("month", VisitModel.visit_datetime))
        .all()
    )

    for month, count in visits:
        monthly_visits[month - 1] = count

    return monthly_visits



@router.post("/record_visit")
def record_visit(employee_id: int, client_id: int, db: Session = Depends(get_db)):
    today_kst = get_kst_today()
    VisitModel = get_visit_model(today_kst.year)

    existing_visit = (
        db.query(VisitModel)
        .filter(VisitModel.employee_id == employee_id)
        .filter(VisitModel.client_id == client_id)
        .filter(VisitModel.visit_date == today_kst)
        .first()
    )

    if existing_visit:
        existing_visit.visit_datetime = get_kst_now()
        db.commit()
        return {"message": "방문 시간 업데이트 완료"}
    else:
        new_visit = VisitModel(
            employee_id=employee_id,
            client_id=client_id,
            visit_datetime=get_kst_now(),
            visit_date=today_kst,
            visit_count=1
        )
        db.add(new_visit)
        db.commit()
        return {"message": "새로운 방문 기록 추가 완료"}
