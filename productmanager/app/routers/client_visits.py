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
