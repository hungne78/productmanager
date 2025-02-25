from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.client_visits import ClientVisit
from app.schemas.client_visits import ClientVisitCreate, ClientVisitOut

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