from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import cast, Date, extract, func, text
from app.db.database import get_db
from app.models.sales_records import SalesRecord
from app.models.products import Product
from app.models.employee_clients import EmployeeClient
from app.schemas.sales import EmployeeClientSalesOut, SalesRecordCreate, SalesRecordOut, SalesOut
from typing import List
from app.models.sales import Sales
from app.models.employees import Employee
from app.routers.auth import get_current_user  # 인증 미들웨어 추가
from app.schemas.employees import EmployeeOut
from app.models.clients import Client
from app.schemas.sales import OutstandingUpdate
from app.models.client_visits import ClientVisit
from app.schemas.sales import SalesAggregateCreate, SaleItem
from app.utils.time_utils import get_kst_now, convert_utc_to_kst 
from app.utils.inventory_service import update_vehicle_stock, subtract_inventory_on_sale
from fastapi.responses import JSONResponse
import json
import logging
from decimal import Decimal  # ✅ Import Decimal
from datetime import timedelta
from typing import Optional
from app.utils.sales_table_utils import get_sales_model

logger = logging.getLogger(__name__)
router = APIRouter()


    
def convert_utc_to_kst(dt: datetime) -> datetime:
    """입력 datetime이 UTC 또는 naive이면 KST로 변환"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=9)))

def decimal_to_float(obj):
    """Helper function to convert Decimal values to float"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def get_kst_today():
    """KST 기준으로 오늘 날짜 가져오기"""
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=9))).date()
# -----------------------------------------------------------------------------
# 1. 특정 직원이 담당하는 거래처들의 매출 조회
# -----------------------------------------------------------------------------

@router.post("/aggregates")
async def get_sales_aggregates(
    request: Request,
    start_date: date = Query(...),
    end_date:   date = Query(...),
    employee_id: Optional[int] = None,
    client_id:   Optional[int] = None,
    db: Session = Depends(get_db)
):
    # ── 1) 연도 목록 산출 ───────────────────────────────
    years = {start_date.year, end_date.year}
    # 두 날짜가 다른 연도를 가리키면 → 두 테이블 UNION 필요
    union_queries = []

    for yr in sorted(years):
        Model = get_sales_model(yr)    # ★ 유틸 호출
        q = (
            db.query(
                func.date(Model.sale_datetime).label("date"),
                func.sum(Model.quantity * Product.default_price).label("sum_sales")
            )
            .join(Product, Model.product_id == Product.id)
            .filter(Model.sale_datetime.between(start_date, end_date))
        )
        if employee_id:
            q = q.filter(Model.employee_id == employee_id)
        if client_id:
            q = q.filter(Model.client_id == client_id)

        union_queries.append(q)

    # ── 2) UNION ALL (연도가 1 개면 그냥 첫 쿼리) ─────────
    if len(union_queries) == 1:
        rows = union_queries[0].group_by("date").all()
    else:
        # SQLAlchemy 2.x 기준
        union_stmt = union_queries[0].union_all(*union_queries[1:]).subquery()
        rows = (
            db.query(
                union_stmt.c.date,
                func.sum(union_stmt.c.sum_sales).label("sum_sales")
            )
            .group_by(union_stmt.c.date)
            .all()
        )

    return [{"date": r.date, "sum_sales": r.sum_sales} for r in rows]

@router.get("/detail/{sale_id}")
async def get_sale_detail(
    sale_id: int,
    year: int = Query(None, description="생략 시 올해"),
    db: Session = Depends(get_db),
):
    try:
        year = year or datetime.now().year
        Model = get_sales_model(year)

        sale = db.query(Model).filter(Model.id == sale_id).first()
        if not sale:
            raise HTTPException(404, "판매 내역을 찾을 수 없습니다.")

        # ─ 관계 속성이 없어도 안전하게 이름 가져오기 ─
        emp_name = getattr(sale, "employee", None).name if hasattr(sale, "employee") \
                   else db.query(Employee).get(sale.employee_id).name
        cli_name = getattr(sale, "client", None).client_name if hasattr(sale, "client") \
                   else db.query(Client).get(sale.client_id).client_name

        # ─ 품목(다건) or 단일 품목 대응 ─
        if hasattr(sale, "items") and sale.items:
            items = [
                {
                    "product_id": i.product_id,
                    "product_name": i.product.product_name,
                    "quantity": i.quantity,
                    "price": i.product.default_price,
                }
                for i in sale.items
            ]
        else:  # 단일 컬럼 구조
            prod = db.query(Product).get(sale.product_id)
            items = [{
                "product_id": sale.product_id,
                "product_name": prod.product_name if prod else "",
                "quantity": sale.quantity,
                "price": prod.default_price if prod else 0,
            }]

        total_price = sum(it["quantity"] * it["price"] for it in items)

        return {
            "sale_id": sale.id,
            "datetime": sale.sale_datetime,
            "employee_id": sale.employee_id,
            "employee_name": emp_name,
            "client_id": sale.client_id,
            "client_name": cli_name,
            "items": items,
            "total_price": total_price,
            "incentive": getattr(sale, "incentive", 0),
        }
    except Exception as e:
        raise HTTPException(400, f"판매 상세 조회 실패: {e}")

    
@router.get("/by_employee/{employee_id}/{sale_date}",
            response_model=List[EmployeeClientSalesOut])
def get_sales_by_employee(
    employee_id: int,
    sale_date: date,
    db: Session = Depends(get_db),
):
    year   = sale_date.year
    Model  = get_sales_model(year)

    client_ids = [
        c[0] for c in db.query(EmployeeClient.client_id)
                        .filter(EmployeeClient.employee_id == employee_id).all()
    ]
    if not client_ids:
        return [{
            "client_id": 0, "client_name": "알 수 없음",
            "total_boxes": 0, "total_sales": 0, "products": []
        }]

    client_map = dict(db.query(Client.id, Client.client_name).all())

    rows = (
        db.query(
            Model.client_id,
            Product.product_name,
            Model.quantity,
            Product.default_price,
        )
        .join(Product, Model.product_id == Product.id)
        .filter(func.date(Model.sale_datetime) == sale_date,
                Model.client_id.in_(client_ids))
        .all()
    )

    if not rows:
        return [{
            "client_id": 0, "client_name": "알 수 없음",
            "total_boxes": 0, "total_sales": 0, "products": []
        }]

    summary = {}
    for r in rows:
        price = (r.default_price or 0) * (r.quantity or 0)
        if r.client_id not in summary:
            summary[r.client_id] = {
                "client_id":   r.client_id,
                "client_name": client_map.get(r.client_id, "알 수 없음"),
                "total_boxes": 0,
                "total_sales": 0,
                "products":    [],
            }
        s = summary[r.client_id]
        s["total_boxes"] += r.quantity
        s["total_sales"] += price
        s["products"].append({"product_name": r.product_name, "quantity": r.quantity})

    return list(summary.values())


# -----------------------------------------------------------------------------
# 2. 새로운 매출 데이터 등록 (단가 자동 계산)
# -----------------------------------------------------------------------------
@router.post("/", response_model=SalesRecordOut)
def create_sales_record(payload: SalesRecordCreate, db: Session = Depends(get_db)):
    """ 새로운 매출 데이터 등록 (KST로 저장) """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    new_sales = SalesRecord(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        sale_datetime=payload.sale_datetime
    )

    db.add(new_sales)
    db.commit()
    db.refresh(new_sales)

    return new_sales  # ✅ 변환 없이 그대로 반환

# -----------------------------------------------------------------------------
# 3. 전체 매출 목록 조회
# -----------------------------------------------------------------------------
@router.get("/", response_model=List[SalesRecordOut])
def list_sales_records(
    year: int = Query(None, description="생략 시 올해"),
    db: Session = Depends(get_db),
):
    Model = get_sales_model(year or datetime.now().year)
    return db.query(Model).all()


# -----------------------------------------------------------------------------
# 4. 특정 직원의 매출 조회
# -----------------------------------------------------------------------------
@router.get("/employee/{employee_id}", response_model=List[SalesOut])
def get_sales_by_employee_all(
    employee_id: int,
    year: int = Query(None),
    db: Session = Depends(get_db),
):
    Model = get_sales_model(year or datetime.now().year)
    return db.query(Model).filter(Model.employee_id == employee_id).all()


# -----------------------------------------------------------------------------
# 5. 특정 날짜의 매출 조회
# -----------------------------------------------------------------------------
@router.get("/date/{sale_date}", response_model=List[SalesOut])
def get_sales_by_date(
    sale_date: date,
    db: Session = Depends(get_db),
):
    Model = get_sales_model(sale_date.year)
    rows = (
        db.query(Model)
          .filter(cast(Model.sale_datetime, Date) == sale_date)
          .all()
    )
    return [convert_sales_to_kst(r) for r in rows]


# ---------------------------------------------------------------------------
# 6. 매출 삭제  ─ year 쿼리파라미터(생략 시 올해)
# ---------------------------------------------------------------------------
@router.delete("/{sales_id}")
def delete_sales_record(
    sales_id: int,
    year: int = Query(None, description="생략 시 올해"),
    db: Session = Depends(get_db),
):
    Model = get_sales_model(year or datetime.now().year)

    obj = db.query(Model).get(sales_id)
    if not obj:
        raise HTTPException(404, "Sales record not found")
    db.delete(obj)
    db.commit()
    return {"detail": "Sales record deleted"}


# ---------------------------------------------------------------------------
# 7. 특정 날짜의 거래처별 판매 품목 목록
# ---------------------------------------------------------------------------
@router.get("/by_client/{sale_date}", response_model=List[SalesOut])
def get_sales_by_client(sale_date: date, db: Session = Depends(get_db)):
    Model = get_sales_model(sale_date.year)

    rows = (
        db.query(
            Model.client_id,
            Model.product_id,
            Product.product_name,
            Model.quantity,
        )
        .join(Product, Model.product_id == Product.id)
        .filter(cast(Model.sale_datetime, Date) == sale_date)
        .all()
    )
    return [
        {
            "client_id": r.client_id,
            "product_id": r.product_id,
            "product_name": r.product_name,
            "quantity": r.quantity,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 8. 특정 날짜의 거래처별 총 매출
# ---------------------------------------------------------------------------
@router.get("/sales/total/{sale_date}")
def get_total_sales(sale_date: date, db: Session = Depends(get_db)):
    Model = get_sales_model(sale_date.year)

    rows = (
        db.query(Model.client_id, Product.default_price, Model.quantity)
        .join(Product, Model.product_id == Product.id)
        .filter(cast(Model.sale_datetime, Date) == sale_date)
        .all()
    )
    agg = {}
    for r in rows:
        agg[r.client_id] = agg.get(r.client_id, 0) + (r.default_price * r.quantity)
    return [{"client_id": cid, "total_sales": amt} for cid, amt in agg.items()]


# ---------------------------------------------------------------------------
# 9‑1. 직원별 월별 매출 합계  (PC 그래프용)
# ---------------------------------------------------------------------------
@router.get("/monthly_sales_pc/{employee_id}/{year}")
def get_monthly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    Model = get_sales_model(year)

    rows = (
        db.query(
            extract("month", Model.sale_datetime).label("m"),
            func.sum(Model.total_amount).label("sum_sales"),
        )
        .filter(Model.employee_id == employee_id)
        .group_by("m")
        .all()
    )
    data = {i + 1: 0 for i in range(12)}
    for r in rows:
        data[int(r.m)] = float(r.sum_sales or 0)
    return data


# ---------------------------------------------------------------------------
# 9‑2. 직원별 ‑ 거래처 연간 총매출
# ---------------------------------------------------------------------------
@router.get("/monthly_sales/{employee_id}/{year}")
def get_yearly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    Model = get_sales_model(year)

    rows = (
        db.query(
            Model.client_id,
            Client.client_name,
            func.sum(Model.quantity).label("boxes"),
            func.sum(Model.return_amount).label("refunds"),
            func.sum(Product.default_price * Model.quantity).label("sales"),
        )
        .join(Product, Model.product_id == Product.id)
        .join(Client, Model.client_id == Client.id)
        .filter(Model.employee_id == employee_id)
        .group_by(Model.client_id, Client.client_name)
        .all()
    )

    out, tot_boxes, tot_ref, tot_sales = [], 0, 0.0, 0.0
    for idx, r in enumerate(rows, 1):
        out.append(
            {
                "index": idx,
                "client_name": r.client_name,
                "total_boxes": int(r.boxes or 0),
                "total_refunds": float(r.refunds or 0),
                "total_sales": float(r.sales or 0),
            }
        )
        tot_boxes += int(r.boxes or 0)
        tot_ref += float(r.refunds or 0)
        tot_sales += float(r.sales or 0)

    if out:
        out.append(
            {
                "index": "합계",
                "client_name": "합계",
                "total_boxes": tot_boxes,
                "total_refunds": tot_ref,
                "total_sales": tot_sales,
            }
        )
    return out


# ---------------------------------------------------------------------------
# 10‑1. 직원별 월‑일자별 매출 (PC 그래프용)
# ---------------------------------------------------------------------------
@router.get("/daily_sales_pc/{employee_id}/{year}/{month}")
def get_daily_sales_pc(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    Model = get_sales_model(year)

    rows = (
        db.query(
            extract("day", Model.sale_datetime).label("d"),
            func.sum(Model.total_amount).label("sum_sales"),
        )
        .filter(Model.employee_id == employee_id)
        .filter(extract("month", Model.sale_datetime) == month)
        .group_by("d")
        .all()
    )
    daily = [0.0] * 31
    for r in rows:
        daily[int(r.d) - 1] = float(r.sum_sales or 0)
    return daily


# ---------------------------------------------------------------------------
# 10‑2. 직원‑거래처‑일자별 상세 매출
# ---------------------------------------------------------------------------
@router.get("/daily_sales/{employee_id}/{year}/{month}")
def get_daily_sales(
    employee_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    Model = get_sales_model(year)

    rows = (
        db.query(
            extract("day", Model.sale_datetime).label("d"),
            Model.client_id,
            Client.client_name,
            func.sum(Model.quantity).label("boxes"),
            func.sum(Model.total_amount).label("sales"),
        )
        .join(Client, Model.client_id == Client.id)
        .filter(Model.employee_id == employee_id)
        .filter(extract("month", Model.sale_datetime) == month)
        .group_by(Model.client_id, Client.client_name, "d")
        .all()
    )

    aggregated = {}
    for r in rows:
        cid, d = r.client_id, str(r.d)
        if cid not in aggregated:
            aggregated[cid] = {
                "client_id": cid,
                "client_name": r.client_name,
                "total_boxes": 0,
                "total_sales": 0,
            }
        ag = aggregated[cid]
        ag[d] = float(r.sales or 0)
        ag["total_boxes"] += int(r.boxes or 0)
        ag["total_sales"] += float(r.sales or 0)

    return JSONResponse(
        content=json.loads(
            json.dumps(list(aggregated.values()), ensure_ascii=False, default=decimal_to_float)
        )
    )

# ------------------------------------------------------------
# 11. 기간별 직원별 총 매출 (연‑도跨 범위 지원)
# ------------------------------------------------------------
@router.get("/sales/employees", response_model=list[dict])
def get_employee_sales(
    db: Session = Depends(get_db),
    start_date: date | None = Query(None),
    end_date:   date | None = Query(None),
):
    # 기본값: 오늘 하루
    start_date = start_date or date.today()
    end_date   = end_date   or date.today()

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # 결과 누적용 dict {emp_id: {"name": str, "total": Decimal}}
    agg: dict[int, dict] = {}

    for yr in range(start_date.year, end_date.year + 1):
        Model = get_sales_model(yr)

        q = (
            db.query(
                Model.employee_id,
                Employee.name.label("employee_name"),
                func.sum(Model.total_amount).label("tot"),
            )
            .join(Employee, Model.employee_id == Employee.id)
            .group_by(Model.employee_id, Employee.name)
        )

        # 연도 내부에서만 날짜 필터
        year_start = max(start_date, date(yr, 1, 1))
        year_end   = min(end_date,   date(yr, 12, 31))
        q = q.filter(cast(Model.sale_datetime, Date) >= year_start)
        q = q.filter(cast(Model.sale_datetime, Date) <= year_end)

        for row in q.all():
            rec = agg.setdefault(
                row.employee_id, {"employee_id": row.employee_id, "employee_name": row.employee_name, "total_sales": 0}
            )
            rec["total_sales"] += float(row.tot or 0)

    return list(agg.values())

# ------------------------------------------------------------
# 12. 기간별 전체 매출 (일자별)
# ------------------------------------------------------------
@router.get("/sales/total", response_model=list[dict])
def get_total_sales(
    db: Session = Depends(get_db),
    start_date: date | None = Query(None),
    end_date:   date | None = Query(None),
):
    start_date = start_date or date.today()
    end_date   = end_date   or date.today()
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    daily_tot: dict[date, float] = {}

    for yr in range(start_date.year, end_date.year + 1):
        Model = get_sales_model(yr)

        year_start = max(start_date, date(yr, 1, 1))
        year_end   = min(end_date,   date(yr, 12, 31))

        rows = (
            db.query(
                cast(Model.sale_datetime, Date).label("d"),
                func.sum(Model.total_amount).label("tot"),
            )
            .filter(cast(Model.sale_datetime, Date).between(year_start, year_end))
            .group_by("d")
            .all()
        )
        for r in rows:
            d = r.d
            daily_tot[d] = daily_tot.get(d, 0) + float(r.tot or 0)

    return [{"date": d.strftime("%Y-%m-%d"), "total_sales": v} for d, v in sorted(daily_tot.items())]

from fastapi.exceptions import RequestValidationError
# -----------------------------------------------------------------------------
# 13. 판매 데이터 등록 (매출 등록 API)
# -----------------------------------------------------------------------------

@router.post("", response_model=SalesRecordOut)
def create_sale(sale_data: SalesRecordCreate, db: Session = Depends(get_db)):
    print("📡 [FastAPI] create_sale() 호출됨")  
    print(f"📡 받은 요청 데이터: {sale_data.model_dump()}")  
    now = get_kst_now()
    today_kst = now.date()
    print(f"🚧 최종 저장 수량 (quantity): {sale_data.quantity}")

    try:
        # ✅ 지원금 처리
        subsidy_amount = sale_data.subsidy_amount if hasattr(sale_data, "subsidy_amount") else 0.0
        is_subsidy = subsidy_amount > 0

        if is_subsidy:
            client = db.query(Client).filter(Client.id == sale_data.client_id).first()
            if client:
                client.outstanding_amount -= subsidy_amount
                db.commit()
                print(f"✅ 지원금 적용 완료: 거래처 {sale_data.client_id}, 지원금 {subsidy_amount}")
            return {"message": "지원금이 적용되었습니다."}

        # ✅ 상품 조회
        product = db.query(Product).filter(Product.id == sale_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
        if not product.box_quantity:
            raise HTTPException(status_code=400, detail="상품의 박스당 개수가 설정되지 않았습니다.")
        from decimal import Decimal
        # ✅ 단가 결정: 고정가 있으면 사용, 없으면 기본가
        # 단가 계산
        if sale_data.client_price and sale_data.client_price > 0:
            unit_price = product.default_price * Decimal(sale_data.client_price) / Decimal("100.0")
        else:
            unit_price = product.default_price
        unit_count = sale_data.box_unit_count if sale_data.box_unit_count else product.box_quantity

        # ✅ 총액 계산: 박스수 * 박스당개수 * 단가
        total_amount = sale_data.quantity * unit_count * unit_price
        print(f"💰 계산된 총 금액: {total_amount:.2f} (박스수={sale_data.quantity}, 개수/박스={unit_count}, 단가={unit_price})")

        # ✅ KST 시간 변환
        sale_datetime_kst = convert_utc_to_kst(sale_data.sale_datetime)
        Model = get_sales_model(sale_datetime_kst.year)  # ← 핵심!


        # ✅ 방문 기록 처리
        existing_visit = (
            db.query(ClientVisit)
            .filter(ClientVisit.employee_id == sale_data.employee_id)
            .filter(ClientVisit.client_id == sale_data.client_id)
            .filter(ClientVisit.visit_date == today_kst)
            .first()
        )

        if existing_visit:
            visit_dt = existing_visit.visit_datetime
            if visit_dt.tzinfo is None:
                visit_dt = visit_dt.replace(tzinfo=now.tzinfo)
            time_diff = now - visit_dt
            if time_diff > timedelta(hours=2):
                existing_visit.visit_count += 1
                print(f"🔼 방문 2시간 경과 → visit_count 증가")
            else:
                print(f"🕒 2시간 이내 재방문 → visit_count 증가 안함")
            existing_visit.visit_datetime = now
            db.commit()
        else:
            new_visit = ClientVisit(
                employee_id=sale_data.employee_id,
                client_id=sale_data.client_id,
                visit_datetime=now,
                visit_date=today_kst,
                visit_count=1
            )
            db.add(new_visit)
            db.flush()
            print(f"✅ 새로운 방문 기록 추가")

        # ✅ 매출 저장 (total_amount 포함)
        new_sale = Model(
            employee_id   = sale_data.employee_id,
            client_id     = sale_data.client_id,
            product_id    = sale_data.product_id,
            quantity      = sale_data.quantity,
            total_amount  = total_amount,
            sale_datetime = sale_datetime_kst,
            return_amount = sale_data.return_amount,
            subsidy_amount= 0.0,
        )
        db.add(new_sale)
        db.flush()
        db.commit()
        db.refresh(new_sale)

        print(f"✅ 매출 저장 완료: ID={new_sale.id}, 총액={new_sale.total_amount:.2f}")

        # ✅ 차량 재고 차감
        subtract_inventory_on_sale(
            employee_id=sale_data.employee_id,
            product_id=sale_data.product_id,
            sold_qty=sale_data.quantity,
            db=db
        )

        return new_sale

    except Exception as e:
        db.rollback()
        print(f"❌ 판매 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"판매 등록 실패: {e}")



def convert_sales_to_kst(sale: SalesRecord, db: Session, visit_id: int):
    """
    SalesRecord 객체의 `sale_datetime`을 그대로 반환 (변환 없음)
    """
    product = db.query(Product).filter(Product.id == sale.product_id).first()
    
    sale_dict = {
        "id": sale.id,
        "employee_id": sale.employee_id,
        "client_id": sale.client_id,
        "product_id": sale.product_id,
        "product_name": product.product_name if product else "Unknown",  # ✅ 제품명 추가
        "quantity": sale.quantity,
        "unit_price": float(product.default_price) if product else 0.0,  # ✅ 단가 추가
        "total_amount": float(sale.quantity * product.default_price) if product else 0.0,  # ✅ 총액 추가
        "sale_datetime": sale.sale_datetime.isoformat() if sale.sale_datetime else None,  # ✅ 변환 없이 반환
        "visit_id": visit_id  # ✅ 방문 기록 ID 포함
    }
    return sale_dict



# -----------------------------------------------------------------------------
# 14. 미수금 업데이트
# -----------------------------------------------------------------------------
@router.put("/outstanding/{client_id}")
def update_outstanding(
    client_id: int,
    update_data: OutstandingUpdate,
    db: Session = Depends(get_db),
    current_user: EmployeeOut = Depends(get_current_user)
):
    print(f"🔹 요청된 클라이언트 ID: {client_id}")
    print(f"🔹 요청된 미수금 업데이트 금액: {update_data.outstanding_amount}")
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        print("❌ 클라이언트를 찾을 수 없음")
        raise HTTPException(status_code=404, detail="Client not found")
    
    if current_user.role not in ["admin", "sales"]:
        print("❌ 권한 없음")
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
    
    client.outstanding_amount = update_data.outstanding_amount
    db.commit()
    
    print(f"✅ 미수금 업데이트 성공: 클라이언트 {client_id}, 새로운 미수금 {update_data.outstanding_amount}")
    return {"detail": "Outstanding amount updated successfully"}


# -----------------------------------------------------------------------------
# 15. 여러 상품 매출 집계 등록
# -----------------------------------------------------------------------------
# ----------------------------------------------------------------------------- 
# 여러 상품을 한 번에 등록 (items 배열 전체) – SalesRecord에 직접 적재
# ----------------------------------------------------------------------------- 
@router.post("/sales/bulk", response_model=list[SalesRecordOut])
def create_bulk_sales(payload: SalesAggregateCreate, db: Session = Depends(get_db)):
    """
    * payload.items : [{product_id, quantity}, …]
    * 각 상품별로 SalesRecord를 INSERT
    """
    # 1) 상품 정보 한꺼번에 조회
    product_ids = [it.product_id for it in payload.items]
    products = (
        db.query(Product)
          .filter(Product.id.in_(product_ids))
          .all()
    )
    product_map = {p.id: p for p in products}

    # 2) 등록
    sale_dt = payload.sale_datetime or datetime.utcnow()
    created: list[SalesRecord] = []

    for it in payload.items:
        product = product_map.get(it.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"상품 {it.product_id} 없음")

        unit_price   = float(product.default_price)
        total_amount = unit_price * it.quantity

        rec = SalesRecord(
            employee_id  = payload.employee_id,
            client_id    = payload.client_id,
            product_id   = it.product_id,
            quantity     = it.quantity,
            total_amount = total_amount,
            sale_datetime= sale_dt,
            return_amount= 0.0,
            subsidy_amount=0.0,
        )
        db.add(rec)
        created.append(rec)

        # 재고 차감
        subtract_inventory_on_sale(
            employee_id = payload.employee_id,
            product_id  = it.product_id,
            sold_qty    = it.quantity,
            db=db,
        )

    db.commit()
    for r in created:
        db.refresh(r)

    return created

# ------------------------------------------------------------
# 16. 특정 거래처 월별 매출
# ------------------------------------------------------------
@router.get("/monthly_sales_client/{client_id}/{year}")
def get_monthly_sales_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    Model = get_sales_model(year)

    rows = (
        db.query(
            extract("month", Model.sale_datetime).label("m"),
            func.sum(Model.total_amount).label("tot"),
        )
        .filter(Model.client_id == client_id)
        .group_by("m")
        .all()
    )

    data = [0.0] * 12
    for r in rows:
        data[int(r.m) - 1] = float(r.tot or 0)
    return data
# -----------------------------------------------------------------------------  
# 17. 특정 거래처 – 해당 연·월의 일자별 매출 합계 (SalesRecord.total_amount 기준)  
# -----------------------------------------------------------------------------  
@router.get("/daily_sales_client/{client_id}/{year}/{month}")
def get_daily_sales_by_client(
    client_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    특정 거래처(client_id)의 연·월별 일자 합계 리스트를 [0..30] 길이로 반환
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    daily_data: list[float] = [0.0] * 31

    rows = (
        db.query(
            extract("day", SalesRecord.sale_datetime).label("sale_day"),
            func.sum(SalesRecord.total_amount).label("sum_sales"),
        )
        .filter(SalesRecord.client_id == client_id)
        .filter(extract("year",  SalesRecord.sale_datetime) == year)
        .filter(extract("month", SalesRecord.sale_datetime) == month)
        .group_by("sale_day")
        .all()
    )

    for sale_day, sum_sales in rows:
        daily_data[int(sale_day) - 1] = float(sum_sales or 0)

    return daily_data


# -----------------------------------------------------------------------------  
# 18. 오늘 날짜 기준 – 특정 거래처의 카테고리별 합계 + 담당사원  
# -----------------------------------------------------------------------------  
@router.get("/today_categories_client/{client_id}")
def get_today_categories_for_client(
    client_id: int,
    db: Session = Depends(get_db),
):
    """
    오늘(KST) 하루 동안의 카테고리별 매출·수량·담당사원
    """
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord

    today_kst = get_kst_today()
    start_dt  = datetime.combine(today_kst, datetime.min.time())
    end_dt    = datetime.combine(today_kst, datetime.max.time())

    rows = (
        db.query(
            Product.category.label("category"),
            func.sum(SalesRecord.total_amount).label("total_amount"),
            func.sum(SalesRecord.quantity).label("total_qty"),
            Employee.name.label("employee_name"),
        )
        .join(SalesRecord, SalesRecord.product_id == Product.id)
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
        .filter(SalesRecord.client_id == client_id)
        .filter(SalesRecord.sale_datetime.between(start_dt, end_dt))
        .group_by(Product.category, Employee.name)
        .all()
    )

    data = [
        {
            "category":       row.category or "기타",
            "total_amount":   float(row.total_amount or 0),
            "total_qty":      int(row.total_qty or 0),
            "employee_name":  row.employee_name or "",
        }
        for row in rows
    ]

    print("📌 오늘 카테고리별 판매 데이터:", data)
    return data


# -----------------------------------------------------------------------------  
# 19. 기간별 직원 매출 합계 (SalesRecord 기준)  
# -----------------------------------------------------------------------------  
@router.get("/employees_records", response_model=list[dict])
def get_employee_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date:   date = Query(None),
):
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord

    q = (
        db.query(
            SalesRecord.employee_id,
            Employee.name.label("employee_name"),
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
    )

    if start_date:
        q = q.filter(SalesRecord.sale_datetime >= start_date)
    if end_date:
        q = q.filter(SalesRecord.sale_datetime <= end_date)

    rows = (
        q.group_by(SalesRecord.employee_id, Employee.name)
         .all()
    )

    return [
        {
            "employee_id":  r.employee_id or 0,
            "employee_name": r.employee_name or "미배정",
            "total_sales":  float(r.total_sales or 0),
        }
        for r in rows
    ]


# -----------------------------------------------------------------------------  
# 20. 기간별 전체 매출 합계 – 일자 단위 (SalesRecord)  
# -----------------------------------------------------------------------------  
@router.get("/total_records", response_model=list[dict])
def get_total_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date:   date = Query(None),
):
    from sqlalchemy import func, cast, Date
    from app.models.sales_records import SalesRecord

    q = (
        db.query(
            cast(SalesRecord.sale_datetime, Date).label("sale_date"),
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
    )

    if start_date:
        q = q.filter(SalesRecord.sale_datetime >= start_date)
    if end_date:
        q = q.filter(SalesRecord.sale_datetime <= end_date)

    rows = (
        q.group_by("sale_date")
         .order_by("sale_date")
         .all()
    )

    return [
        {
            "date":        row.sale_date.strftime("%Y-%m-%d"),
            "total_sales": float(row.total_sales or 0),
        }
        for row in rows
    ]


# -----------------------------------------------------------------------------  
# 21. 기간별 거래처 매출 합계 (SalesRecord)  
# -----------------------------------------------------------------------------  
@router.get("/by_client_range", response_model=list[dict])
def get_sales_by_client_range(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date:   date = Query(...),
):
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord

    q = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
        .join(Client, SalesRecord.client_id == Client.id)
        .filter(SalesRecord.sale_datetime >= start_date)
        .filter(SalesRecord.sale_datetime <= end_date)
        .group_by(SalesRecord.client_id, Client.client_name)
    )

    rows = q.all()

    return [
        {
            "client_id":   r.client_id,
            "client_name": r.client_name,
            "total_sales": float(r.total_sales or 0),
        }
        for r in rows
    ]

# =============================================================================
# 22. 특정 연‑월 거래처별 세금계산서(매출) 집계
# =============================================================================
@router.get("/clients/{year}/{month}")
def get_clients_invoices(
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    지정 연・월에 대한 거래처별 매출 총액·VAT(10%) 목록 반환
    """
    import calendar
    from datetime import date
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord
    from app.models.clients import Client

    # ▶ 날짜 범위: 그 달 1일 ~ 마지막 날
    start_date = date(year, month, 1)
    end_date   = date(year, month, calendar.monthrange(year, month)[1])

    rows = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            Client.representative_name.label("client_ceo"),
            Client.business_number,
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
        .join(Client, SalesRecord.client_id == Client.id)
        .filter(SalesRecord.sale_datetime.between(start_date, end_date))
        .group_by(
            SalesRecord.client_id,
            Client.client_name,
            Client.representative_name,
            Client.business_number,
        )
        .all()
    )

    invoices: list[dict] = []
    for r in rows:
        total = float(r.total_sales or 0)
        vat   = round(total * 0.1, 2)
        invoices.append(
            {
                "supplier_id":    "",          # 필요 시 채워넣으세요
                "supplier_name":  "",
                "supplier_ceo":   "",
                "client_id":      str(r.client_id),
                "client_name":    r.client_name,
                "client_ceo":     r.client_ceo,
                "business_number": r.business_number,
                "total_sales":    total,
                "tax_amount":     vat,
            }
        )

    return invoices


# =============================================================================
# 23. 직원 기준 월/전월/전년동월 매출 + 방문주기
# =============================================================================
@router.get("/employee_sales/{employee_id}/{year}/{month}")
def get_employee_sales_data(
    employee_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    직원이 담당하는 거래처들의
      · 전월 매출
      · 전년동월 매출
      · 이번 달 매출
      · 평균 방문 주기(일 단위)
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    # 담당 거래처 ID 목록
    client_ids = [
        cid for (cid,) in db.query(EmployeeClient.client_id)
                           .filter(EmployeeClient.employee_id == employee_id)
                           .all()
    ]
    if not client_ids:
        return []

    # 공통 쿼리 빌더
    def month_sum(target_year: int, target_month: int):
        return (
            db.query(
                SalesRecord.client_id,
                func.sum(SalesRecord.total_amount).label("total_sales"),
            )
            .filter(SalesRecord.client_id.in_(client_ids))
            .filter(extract("year",  SalesRecord.sale_datetime) == target_year)
            .filter(extract("month", SalesRecord.sale_datetime) == target_month)
            .group_by(SalesRecord.client_id)
            .all()
        )

    # ▷ 이번 달 / 전월 / 전년동월
    current   = month_sum(year, month)
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    prev      = month_sum(prev_year, prev_month)
    last_year = month_sum(year - 1, month)

    # 매출 dict化 {client_id: total}
    def to_map(rows): return {cid: float(t or 0) for cid, t in rows}
    map_current   = to_map(current)
    map_prev      = to_map(prev)
    map_last_year = to_map(last_year)

    # 방문 주기(일)
    visit_freq: dict[int, float] = {}
    for cid in client_ids:
        visits = (
            db.query(ClientVisit.visit_datetime)
              .filter(ClientVisit.client_id == cid)
              .order_by(ClientVisit.visit_datetime)
              .all()
        )
        if len(visits) > 1:
            gaps = [
                (visits[i].visit_datetime - visits[i - 1].visit_datetime).days
                for i in range(1, len(visits))
            ]
            visit_freq[cid] = sum(gaps) / len(gaps)
        else:
            visit_freq[cid] = 0.0

    # 최종 결과
    results: list[dict] = []
    for cid in client_ids:
        results.append(
            {
                "client_id":            cid,
                "client_name":          db.query(Client.client_name)
                                          .filter(Client.id == cid)
                                          .scalar(),
                "prev_month_sales":     map_prev.get(cid, 0),
                "last_year_sales":      map_last_year.get(cid, 0),
                "current_month_sales":  map_current.get(cid, 0),
                "visit_frequency":      visit_freq.get(cid, 0),
            }
        )
    return results


# =============================================================================
# 24. 모든 직원의 ‘이번 달’ 매출 합계
# =============================================================================
@router.get("/monthly_sales")
def fetch_monthly_sales(db: Session = Depends(get_db)):
    """
    (KST) 현재 월의 직원별 매출 총합
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    today = get_kst_today()
    year, month = today.year, today.month

    rows = (
        db.query(
            SalesRecord.employee_id,
            Employee.name.label("employee_name"),
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
        .join(Employee, SalesRecord.employee_id == Employee.id)
        .filter(extract("year",  SalesRecord.sale_datetime) == year)
        .filter(extract("month", SalesRecord.sale_datetime) == month)
        .group_by(SalesRecord.employee_id, Employee.name)
        .all()
    )

    return [
        {
            "employee_id":  r.employee_id,
            "employee_name": r.employee_name,
            "total_sales":  float(r.total_sales or 0),
        }
        for r in rows
    ]


# =============================================================================
# 25. 직원이 담당하는 거래처별 해당 월 매출 합계
# =============================================================================
@router.get("/employee_clients_sales/{employee_id}/{year}/{month}")
def employee_clients_month_sales(
    employee_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    직원(employee_id)의 거래처별 월 매출 합계
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    # 담당 거래처
    client_ids = [
        cid for (cid,) in db.query(EmployeeClient.client_id)
                           .filter(EmployeeClient.employee_id == employee_id)
                           .all()
    ]
    if not client_ids:
        return []

    rows = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            func.sum(SalesRecord.total_amount).label("total_sales"),
        )
        .join(Client, SalesRecord.client_id == Client.id)
        .filter(SalesRecord.client_id.in_(client_ids))
        .filter(extract("year",  SalesRecord.sale_datetime) == year)
        .filter(extract("month", SalesRecord.sale_datetime) == month)
        .group_by(SalesRecord.client_id, Client.client_name)
        .all()
    )

    return [
        {
            "client_id":   r.client_id,
            "client_name": r.client_name,
            "total_sales": float(r.total_sales or 0),
        }
        for r in rows
    ]


# =============================================================================
# 26. (참고) 직원별 미수금 현황 – 기존 로직 그대로
# =============================================================================
@router.get("/outstanding/{employee_id}")
def get_outstanding_balances(
    employee_id: int,
    db: Session = Depends(get_db),
):
    results = (
        db.query(Client.client_name, Client.outstanding_amount)
          .join(EmployeeClient, EmployeeClient.client_id == Client.id)
          .filter(EmployeeClient.employee_id == employee_id)
          .all()
    )

    return JSONResponse(
        content=[
            {
                "client_name": r.client_name.strip(),
                "outstanding": float(r.outstanding_amount or 0),
            }
            for r in results
        ],
        media_type="application/json; charset=utf-8",
    )


@router.get("/employee_clients_sales")
def get_client_sales(
    employee_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    직원(employee_id)이 담당하는 거래처들의 연간 월별 매출과 미수금(outstanding_amount) 포함 (total_amount 기준)
    """
    from app.models.clients import Client
    from sqlalchemy import extract, func
    

    # 1️⃣ 직원 담당 거래처 목록 조회
    employee_client_rows = (
        db.query(EmployeeClient.client_id, Client.client_name, Client.outstanding_amount)
        .join(Client, EmployeeClient.client_id == Client.id)
        .filter(EmployeeClient.employee_id == employee_id)
        .all()
    )

    if not employee_client_rows:
        return {
            "year": year,
            "per_client": {},
            "total_monthly": [0]*12,
            "client_names": {},
            "outstanding_map": {}
        }

    client_ids = []
    client_names = {}
    outstanding_map = {}
    for row in employee_client_rows:
        cid = row.client_id
        client_ids.append(cid)
        client_names[cid] = row.client_name
        outstanding_map[cid] = float(row.outstanding_amount or 0.0)

    # 2️⃣ 연간 매출 조회 (total_amount 기준)
    results = (
        db.query(
            SalesRecord.client_id.label("cid"),
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(SalesRecord.total_amount).label('sum_sales')
        )
        .filter(SalesRecord.client_id.in_(client_ids))
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by(SalesRecord.client_id, extract('month', SalesRecord.sale_datetime))
        .all()
    )

    # 3️⃣ 거래처별 월 매출 저장
    per_client = {cid: [0]*12 for cid in client_ids}
    for row in results:
        m = int(row.sale_month)
        per_client[int(row.cid)][m - 1] = float(row.sum_sales or 0)

    # 4️⃣ 전체 합계 계산
    total_monthly = [0]*12
    for values in per_client.values():
        for i in range(12):
            total_monthly[i] += values[i]

    return {
        "year": year,
        "per_client": per_client,
        "total_monthly": total_monthly,
        "client_names": client_names,
        "outstanding_map": outstanding_map
    }


# -------------------------------------------------------------------------
# 24‑BIS. 특정 거래처의 월 매출 총합 (total_amount 기준으로 교체)
# -------------------------------------------------------------------------
@router.get("/client_monthly_sales")
def get_client_monthly_sales(
    client_id: int = Query(...),
    year: int   = Query(...),
    month: int  = Query(...),
    db: Session = Depends(get_db),
):
    """
    지정 거래처(client_id)의 year‑month 매출 총액을 반환
    ▶ 반환 예시: { "total_sales": 12345.0 }
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    sum_val = (
        db.query(func.sum(SalesRecord.total_amount))
          .filter(SalesRecord.client_id == client_id)
          .filter(extract("year",  SalesRecord.sale_datetime) == year)
          .filter(extract("month", SalesRecord.sale_datetime) == month)
          .scalar()
    )

    return {"total_sales": float(sum_val or 0.0)}


@router.get("/monthly_box_count_client/{client_id}/{year}")
def get_monthly_box_count(client_id: int, year: int, db: Session = Depends(get_db)):
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(SalesRecord.quantity).label('total_boxes')
        )
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by(extract('month', SalesRecord.sale_datetime))
        .all()
    )
    monthly_boxes = [0] * 12
    for row in results:
        m = int(row.sale_month) - 1
        monthly_boxes[m] = int(row.total_boxes or 0)
    return monthly_boxes
