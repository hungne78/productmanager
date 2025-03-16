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
from app.utils.time_utils import convert_utc_to_kst, get_kst_today  # ✅ UTC → KST 변환 함수 추가

router = APIRouter()

@router.post("/", response_model=ClientVisitOut)
def create_client_visit(payload: ClientVisitCreate, db: Session = Depends(get_db)):
    """ 방문 기록 추가 (KST로 저장) """
    new_visit = ClientVisit(
        employee_id=payload.id,
        client_id=payload.client_id,
        visit_datetime=payload.visit_datetime,  # ✅ KST로 저장됨
        order_id=payload.order_id
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    return new_visit  # ✅ 변환 없이 KST 그대로 반환

@router.get("/", response_model=list[ClientVisitOut])
def list_client_visits(db: Session = Depends(get_db)):
    """ 모든 방문 기록 조회 (KST 그대로 반환) """
    visits = db.query(ClientVisit).all()
    return visits  # ✅ 변환 없이 그대로 반환


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

def get_kst_today():
    """현재 날짜를 KST(Asia/Seoul) 기준으로 변환"""
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9))).date()



@router.get("/today_visits_details")
def get_today_visits_details(
    employee_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """ 오늘(KST) 방문한 거래처 목록 조회 (개별 방문 기록 유지) """

    today_kst = get_kst_today()
    print(f"🔍 KST 기준 오늘 날짜: {today_kst}")

    query = (
        db.query(
            ClientVisit.id.label("visit_id"),
            ClientVisit.visit_datetime,
            ClientVisit.visit_count,  # ✅ 방문 횟수 추가
            Client.id.label("client_id"),
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
            & (cast(SalesRecord.sale_datetime, Date) == cast(ClientVisit.visit_datetime, Date))
        )
        .outerjoin(Product, Product.id == SalesRecord.product_id)
        .filter(ClientVisit.employee_id == employee_id)
        .filter(ClientVisit.visit_date == today_kst)  # ✅ 오늘 방문 데이터만 조회
        .group_by(ClientVisit.id, ClientVisit.visit_datetime, ClientVisit.visit_count, Client.id, Client.client_name, Client.outstanding_amount)  # ✅ 방문 기록 개별 출력
        .all()
    )

    results = []
    for row in query:
        visit_datetime_kst = row.visit_datetime.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9))) if row.visit_datetime else None

        results.append({
            "visit_id": row.visit_id,
            "visit_datetime": visit_datetime_kst.strftime("%Y-%m-%d %H:%M:%S") if visit_datetime_kst else "방문 기록 없음",
            "visit_count": row.visit_count,  # ✅ 방문 횟수 반환 추가
            "client_id": row.client_id,
            "client_name": row.client_name,
            "outstanding_amount": float(row.outstanding_amount or 0),
            "today_sales": float(row.today_sales or 0),
        })

    print(f"📝 조회된 방문 기록: {len(results)}개")

    return results




@router.get("/monthly_visits_client/{client_id}/{year}")
def get_monthly_visits_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    """ 클라이언트 기준 월별 방문 조회 API """
    
    # ✅ 기본적으로 12개월(1~12월) 데이터를 0으로 초기화
    monthly_visits = [0] * 12  

    # ✅ 데이터베이스에서 방문 기록 조회
    visits = (
        db.query(extract("month", ClientVisit.visit_datetime), func.count())
        .filter(ClientVisit.client_id == client_id)
        .filter(extract("year", ClientVisit.visit_datetime) == year)
        .group_by(extract("month", ClientVisit.visit_datetime))
        .all()
    )

    # ✅ 조회된 방문 데이터를 리스트에 적용
    for month, count in visits:
        monthly_visits[month - 1] = count  # `month-1` (0부터 시작하는 인덱스 맞추기)

    return monthly_visits


@router.post("/record_visit")
def record_visit(
    employee_id: int,
    client_id: int,
    db: Session = Depends(get_db)
):
    """ 직원이 거래처를 방문하면 방문 기록을 추가 또는 업데이트 """

    today_kst = get_kst_today().date()  # ✅ KST 기준 오늘 날짜

    # ✅ 같은 직원, 같은 거래처, 같은 날짜 방문 여부 확인
    existing_visit = (
        db.query(ClientVisit)
        .filter(ClientVisit.employee_id == employee_id)
        .filter(ClientVisit.client_id == client_id)
        .filter(ClientVisit.visit_date == today_kst)  # ✅ 같은 날짜 비교
        .first()
    )

    if existing_visit:
        # ✅ 같은 날 방문한 기록이 있으면 visit_datetime만 업데이트 (visit_count는 유지)
        existing_visit.visit_datetime = get_kst_now()
        db.commit()
        print(f"🔄 기존 방문 기록 업데이트: 직원 {employee_id}, 거래처 {client_id}, 날짜 {today_kst}, 새로운 시간 {existing_visit.visit_datetime}")
    else:
        # ✅ 기존 방문 기록이 없으면 새로운 방문 기록 생성
        new_visit = ClientVisit(
            employee_id=employee_id,
            client_id=client_id,
            visit_datetime=get_kst_now(),
            visit_date=today_kst,  # ✅ 날짜만 저장 (중복 방지)
            visit_count=1  # ✅ 새로운 방문은 1부터 시작
        )
        db.add(new_visit)
        db.commit()
        print(f"✅ 새로운 방문 기록 추가: 직원 {employee_id}, 거래처 {client_id}, 날짜 {today_kst}")

    return {"message": "방문 기록 완료"}
