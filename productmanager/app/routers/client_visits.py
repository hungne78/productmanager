from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client_visits import ClientVisit
from app.models.clients import Client
from typing import List
from app.schemas.client_visits import ClientVisitCreate, ClientVisitOut
from sqlalchemy import func, cast, Date
from datetime import date
from app.models.sales_records import SalesRecord
from app.models.products import Product

router = APIRouter()

@router.post("/", response_model=ClientVisitOut)
def create_client_visit(payload: ClientVisitCreate, db: Session = Depends(get_db)):
    new_visit = ClientVisit(
        employee_id=payload.id,
        client_id=payload.client_id,
        visit_datetime=payload.visit_datetime,
        order_id=payload.order_id
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    result = new_visit.__dict__.copy()
    result["id_employee"] = result.pop("employee_id")
    return result

@router.get("/", response_model=list[ClientVisitOut])
def list_client_visits(db: Session = Depends(get_db)):
    visits = db.query(ClientVisit).all()
    return visits

@router.get("/{visit_id}", response_model=ClientVisitOut)
def get_client_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(ClientVisit).get(visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Client Visit not found")
    return visit
# client_visits.py
from sqlalchemy import extract, func

@router.get("/monthly_visits/{employee_id}/{year}")
def get_monthly_visits(employee_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 직원의 해당 연도 월별 방문 횟수
    예: [10, 8, 12, ... 12개]
    """
    results = (
        db.query(
            extract('month', ClientVisit.visit_datetime).label('visit_month'),
            func.count(ClientVisit.id).label('cnt')
        )
        .filter(ClientVisit.employee_id == employee_id)
        .filter(extract('year', ClientVisit.visit_datetime) == year)
        .group_by(extract('month', ClientVisit.visit_datetime))
        .all()
    )

    monthly_counts = [0]*12
    for row in results:
        m = int(row.visit_month) - 1
        monthly_counts[m] = row.cnt

    return monthly_counts


@router.get("/daily_visits/{employee_id}/{year}/{month}")
def get_daily_visits(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 직원의 해당 월 일자별 방문 횟수
    예: [0, 2, 0, 1, 3, ...] 31개 (최대 31일)
    """
    daily_counts = [0]*31

    results = (
        db.query(
            extract('day', ClientVisit.visit_datetime).label('visit_day'),
            func.count(ClientVisit.id).label('cnt')
        )
        .filter(ClientVisit.employee_id == employee_id)
        .filter(extract('year', ClientVisit.visit_datetime) == year)
        .filter(extract('month', ClientVisit.visit_datetime) == month)
        .group_by(extract('day', ClientVisit.visit_datetime))
        .all()
    )

    for row in results:
        d = int(row.visit_day) - 1
        daily_counts[d] = row.cnt

    return daily_counts

@router.get("/today_visits_details")
def get_today_visits_details(
    employee_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    '오늘(date.today())' 날짜에 해당 직원(employee_id)이 방문한 거래처 목록에 대해:
    - visit_datetime (방문일시)
    - 거래처명(client_name)
    - 미수금(outstanding_amount)
    - "오늘 매출" 합계(today_sales)
      (sales_records에서 sale_date=오늘, employee_id 동일, client_id 동일)
    를 한 번에 반환.
    """

    today = date.today()

    # LEFT JOIN(outerjoin)으로 sales_records, product를 묶고,
    # GROUP BY로 p.default_price * sr.quantity를 합산
    # (예: ClientVisit.visit_datetime의 날짜 부분 == sale_date 면 같은 날로 간주)
    # 여기서는 “visit_datetime의 date” == “sale_date” 로 매칭하는 식으로 처리
    query = (
        db.query(
            ClientVisit.id.label("visit_id"),
            ClientVisit.visit_datetime,
            Client.client_id,
            Client.client_name,
            Client.outstanding_amount,
            func.coalesce(
                func.sum(Product.default_price * SalesRecord.quantity), 0
            ).label("today_sales")
        )
        .join(Client, ClientVisit.client_id == Client.id)
        .outerjoin(
            SalesRecord,
            (SalesRecord.client_id == ClientVisit.client_id)
            & (SalesRecord.employee_id == ClientVisit.employee_id)
            & (cast(SalesRecord.sale_date, Date) == cast(ClientVisit.visit_datetime, Date))
        )
        .outerjoin(Product, Product.id == SalesRecord.product_id)
        .filter(ClientVisit.employee_id == employee_id)
        .filter(cast(ClientVisit.visit_datetime, Date) == today)
        .group_by(
            ClientVisit.id,
            ClientVisit.visit_datetime,
            Client.id,                # client_id
            Client.client_name,
            Client.outstanding_amount
        )
        .order_by(ClientVisit.visit_datetime.asc())
    )

    rows = query.all()
    results = []
    for row in rows:
        # 방문일시를 문자열로 변환
        visit_time_str = row.visit_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # Decimal -> float 변환
        out_amt = float(row.outstanding_amount or 0)
        sales_amt = float(row.today_sales or 0)

        results.append({
            "visit_id": row.visit_id,
            "visit_datetime": visit_time_str,
            "client_id": row.client_id,
            "client_name": row.client_name,
            "outstanding_amount": out_amt,
            "today_sales": sales_amt,
        })

    return results