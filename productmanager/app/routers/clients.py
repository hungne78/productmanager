from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientOut, ClientUpdate
from fastapi.responses import JSONResponse
from app.models.employee_clients import EmployeeClient
from app.utils.time_utils import convert_utc_to_kst
from starlette.responses import JSONResponse, StreamingResponse
import json
from typing import List
from passlib.hash import bcrypt
from geopy.geocoders import Nominatim  # 또는 Kakao / Google / Naver 등
from geopy.extra.rate_limiter import RateLimiter
from app.models.employees import Employee
import requests
KAKAO_REST_API_KEY = "35cb475df605091f2b811aa7185bc6bf"
geolocator = Nominatim(user_agent="icemanager3/(hungne@naver.com)")   # 서비스에 맞춰 변경
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def geocode_address(address: str) -> tuple[float | None, float | None]:
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {"query": address}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        documents = resp.json().get("documents", [])

        if documents:
            first = documents[0]
            lat = float(first.get("y", 0))
            lon = float(first.get("x", 0))

            # 유효 좌표 범위 검사
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon

            print(f"⚠️ 좌표 범위 이상: lat={lat}, lon={lon}")
    except Exception as e:
        print(f"❌ Kakao 지오코딩 실패: {e}")

    return None, None


router = APIRouter()

@router.get("/by_employee")
def get_clients_grouped_by_employee(db: Session = Depends(get_db)):
    from app.models.employees import Employee
    from app.models.employee_clients import EmployeeClient
    from app.models.clients import Client

    result = []

    employees = db.query(Employee).all()
    for emp in employees:
        emp_clients = (
            db.query(Client)
            .join(EmployeeClient, EmployeeClient.client_id == Client.id)
            .filter(EmployeeClient.employee_id == emp.id)
            .all()
        )

        clients_list = [
            {
                "client_id": c.id,
                "client_name": c.client_name,
                "region": getattr(c, "region", ""),  # region 필드가 있다고 가정
                "outstanding": int(c.outstanding_amount or 0)
            }
            for c in emp_clients
        ]

        result.append({
            "employee_id": emp.id,
            "employee_name": emp.name,
            "clients": clients_list
        })

    return result

@router.post("/", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """ 새로운 거래처 등록 (KST로 저장) """
    password_hash = bcrypt.hash("1234")
    lat, lng = geocode_address(payload.address)
    new_client = Client(
        client_name=payload.client_name,
        representative_name=payload.representative_name,
        address=payload.address,
        phone=payload.phone,
        outstanding_amount=payload.outstanding_amount,
        regular_price=payload.regular_price,
        fixed_price=payload.fixed_price,
        business_number=payload.business_number,
        email=payload.email,
        password_hash=password_hash,
        latitude = lat,
        longitude = lng,
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client  # ✅ 변환 없이 그대로 반환

@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """ 모든 거래처 목록 조회 (KST 그대로 반환) """
    clients = db.query(Client).all()
    return clients  # ✅ 변환 없이 그대로 반환


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """ 특정 거래처 조회 (KST 변환 없음) """
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client  # ✅ 변환 없이 그대로 반환


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    """ 거래처 정보 수정 + 비밀번호 변경 """
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_client.client_name = payload.client_name
    db_client.representative_name = payload.representative_name
    db_client.address = payload.address
    db_client.phone = payload.phone
    db_client.outstanding_amount = payload.outstanding_amount
    db_client.regular_price = payload.regular_price
    db_client.fixed_price = payload.fixed_price
    db_client.business_number = payload.business_number
    db_client.email = payload.email

    # ✅ 비밀번호 변경 시
    if payload.password:
        db_client.password_hash = bcrypt.hash(payload.password)
    if payload.address != db_client.address:
        lat, lng = geocode_address(payload.address)
        db_client.latitude  = lat
        db_client.longitude = lng

    db_client.address = payload.address
    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """ 특정 거래처 삭제 (연결된 직원-거래처 정보 먼저 삭제) """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다.")

    try:
        # ✅ 연결된 직원-거래처 관계 삭제
        db.query(EmployeeClient).filter(EmployeeClient.client_id == client_id).delete()

        # ✅ 거래처 삭제
        db.delete(client)
        db.commit()

        return {"message": "거래처가 삭제되었습니다."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"거래처 삭제 실패: {str(e)}")

@router.put("/{client_id}/outstanding")
def update_outstanding(client_id: int, payload: dict, db: Session = Depends(get_db)):
    """ 거래처 미수금(outstanding_amount) 업데이트 """
    db_client = db.query(Client).filter(Client.id == client_id).first()

    if not db_client:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다.")

    if "outstanding_amount" not in payload:
        raise HTTPException(status_code=400, detail="outstanding_amount 필드가 필요합니다.")

    try:
        db_client.outstanding_amount = payload["outstanding_amount"]
        db.commit()
        db.refresh(db_client)

        return {"message": "미수금이 업데이트되었습니다.", "outstanding_amount": db_client.outstanding_amount}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"미수금 업데이트 실패: {str(e)}")
@router.get("/all/{employee_id}", response_model=List[dict])
def get_all_clients(employee_id: int, db: Session = Depends(get_db)):
    """
    특정 직원이 담당하는 모든 거래처 목록 반환
    """
    from sqlalchemy.orm import joinedload

    print(f"📌 [API CALL] GET /clients/all/{employee_id}")

    clients = (
        db.query(Client.id, Client.client_name)
        .join(EmployeeClient, EmployeeClient.client_id == Client.id)
        .filter(EmployeeClient.employee_id == employee_id)
        .all()
    )

    if not clients:
        print.warning(f"⚠️ No clients found for employee {employee_id}")
        return []

    response_data = [{"client_id": c.id, "client_name": c.client_name.strip()} for c in clients]

    print(f"📌 Final API Response: {response_data}")
    return response_data


@router.get("/{client_id}/detail")
def get_client_detail(client_id: int, db: Session = Depends(get_db)):
    from app.models.clients import Client
    from app.models.employee_clients import EmployeeClient
    from app.models.employees import Employee
    from app.models.sales_records import SalesRecord
    from sqlalchemy import desc

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="거래처를 찾을 수 없습니다.")

    # 담당 직원 목록
    emp_links = (
        db.query(EmployeeClient)
        .filter(EmployeeClient.client_id == client_id)
        .all()
    )
    employees = [
        {
            "employee_id": link.employee_id,
            "employee_name": db.query(Employee).get(link.employee_id).name
        } for link in emp_links
    ]

    # 최근 매출
    recent_sales = (
        db.query(SalesRecord)
        .filter(SalesRecord.client_id == client_id)
        .order_by(desc(SalesRecord.sale_datetime))
        .limit(10)
        .all()
    )
    sales_data = [
        {
            "date": sr.sale_datetime.date().isoformat(),
            "amount": int(sr.quantity * sr.product.default_price),
            "products": [  # 실제로는 조인 필요
                {"product_name": sr.product.product_name, "qty": sr.quantity}
            ]
        } for sr in recent_sales
    ]

    # 최근 방문
    visit_data = [
        {
            "date": sr.sale_datetime.date().isoformat(),
            "employee_id": sr.employee_id
        }
        for sr in recent_sales
    ]

    return {
        "client_id": client.id,
        "client_name": client.client_name,
        "representative": client.representative_name,
        "business_number": client.business_number,
        "address": client.address,
        "phone": client.phone,
        "outstanding": int(client.outstanding_amount or 0),
        "employees": employees,
        "recent_sales": sales_data,
        "visits": visit_data
    }
from decimal import Decimal

@router.get("/monthly_sales_client/{client_id}/{year}")
def get_monthly_sales(client_id: int, year: int, db: Session = Depends(get_db)):
    from app.models.sales_records import SalesRecord
    from app.models.products import Product
    from sqlalchemy import extract

    monthly = [0.0] * 12

    records = (
        db.query(SalesRecord, Product)
        .join(Product, Product.id == SalesRecord.product_id)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract("year", SalesRecord.sale_datetime) == year)
        .all()
    )

    for sr, prod in records:
        month_idx = sr.sale_datetime.month - 1
        price = float(prod.default_price or 0)
        quantity = sr.quantity or 0
        monthly[month_idx] += price * quantity

    return [round(m, 2) for m in monthly]
@router.get("/monthly_visits_client/{client_id}/{year}")
def get_monthly_visits(client_id: int, year: int, db: Session = Depends(get_db)):
    from app.models.sales_records import SalesRecord
    from sqlalchemy import func, extract

    monthly_visits = [0] * 12

    visit_data = (
        db.query(func.date(SalesRecord.sale_datetime))
        .filter(SalesRecord.client_id == client_id)
        .filter(extract("year", SalesRecord.sale_datetime) == year)
        .distinct()
        .all()
    )

    for (visit_date_str,) in visit_data:
        visit_date = datetime.strptime(visit_date_str, "%Y-%m-%d")
        monthly_visits[visit_date.month - 1] += 1

    return monthly_visits
@router.get("/monthly_box_count_client/{client_id}/{year}")
def get_monthly_box_count(client_id: int, year: int, db: Session = Depends(get_db)):
    from app.models.sales_records import SalesRecord
    from sqlalchemy import extract

    monthly = [0] * 12

    records = (
        db.query(SalesRecord)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract("year", SalesRecord.sale_datetime) == year)
        .all()
    )

    for r in records:
        monthly[r.sale_datetime.month - 1] += r.quantity or 0

    return monthly

@router.get("/map/clients", response_model=list[dict])
def clients_for_map(db: Session = Depends(get_db)):
    """
    좌표‧담당직원 정보를 포함한 거래처 목록
    """
    data = (
        db.query(
            Client.id.label("client_id"),
            Client.client_name,
            Client.latitude.label("lat"),
            Client.longitude.label("lon"),
            Employee.id.label("employee_id"),
            Employee.name.label("employee_name")
        )
        .join(EmployeeClient, EmployeeClient.client_id == Client.id)
        .join(Employee, Employee.id == EmployeeClient.employee_id)
        .filter(Client.latitude.isnot(None), Client.longitude.isnot(None))  # ⬅️ 좌표 없는 거래처 제외
        .all()
    )

    return [
        {
            "client_id": c.client_id,
            "client_name": c.client_name,
            "lat": c.lat,
            "lon": c.lon,
            "employee_id": c.employee_id,
            "employee_name": c.employee_name
        }
        for c in data
    ]