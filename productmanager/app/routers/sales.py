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
    start_date: date = Query(...),  # 쿼리 파라미터로 날짜 받기
    end_date: date = Query(...),    # 쿼리 파라미터로 날짜 받기
    employee_id: Optional[int] = None,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db)  # DB 연결
):
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(status_code=400, detail="Token is required")
    token = token.split(" ")[1] if token.startswith("Bearer") else token

    try:
        query = db.query(
            func.date(SalesRecord.sale_datetime).label("date"),
            func.sum(SalesRecord.quantity * Product.default_price).label("sum_sales"),
            func.group_concat(  # GROUP_CONCAT()을 사용하여 문자열 결합
                func.concat(
                    '{"sale_id":', SalesRecord.id,
                    ',"product_name":"', Product.product_name,
                    '","quantity":', SalesRecord.quantity,
                    ',"price":', Product.default_price,
                    '}'
                ), ','
            ).label("items")  # 결과를 쉼표로 구분된 문자열로 결합
        ).join(Product, SalesRecord.product_id == Product.id)

        query = query.filter(
            SalesRecord.sale_datetime >= start_date,
            SalesRecord.sale_datetime <= end_date
        )

        if employee_id:
            query = query.filter(SalesRecord.employee_id == employee_id)
        if client_id:
            query = query.filter(SalesRecord.client_id == client_id)

        results = query.group_by(func.date(SalesRecord.sale_datetime)).all()

        # JSON 직렬화 처리: SQLAlchemy 모델을 dict로 변환
        def serialize_row(row):
            return {
                "date": row.date,
                "sum_sales": row.sum_sales,
                "items": row.items
            }

        serialized_results = [serialize_row(row) for row in results]

        return {"by_date": serialized_results}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"판매 집계 조회 실패: {e}")
    
@router.get("/detail/{sale_id}")
async def get_sale_detail(sale_id: int, db: Session = Depends(get_db)):
    try:
        sale = db.query(SalesRecord).filter(SalesRecord.id == sale_id).first()

        if not sale:
            raise HTTPException(status_code=404, detail="판매 내역을 찾을 수 없습니다.")

        return {
            "sale_id": sale.id,
            "datetime": sale.sale_datetime,
            "employee_id": sale.employee_id,
            "employee_name": sale.employee.name,
            "client_id": sale.client_id,
            "client_name": sale.client.client_name,
            "items": [{"product_id": item.product_id, "product_name": item.product.product_name, "quantity": item.quantity, "price": item.product.default_price} for item in sale.items],
            "total_price": sum(item.quantity * item.product.default_price for item in sale.items),
            "incentive": sale.incentive,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"판매 상세 조회 실패: {e}")
    
@router.get("/by_employee/{employee_id}/{sale_date}", response_model=List[EmployeeClientSalesOut])
def get_sales_by_employee(employee_id: int, sale_date: date, db: Session = Depends(get_db)):
    """
    특정 직원이 담당하는 거래처들의 매출 데이터를 조회합니다.
    """
    client_data = db.query(Client.id, Client.client_name).all()
    client_map = {c.id: c.client_name for c in client_data}

    client_ids = [c[0] for c in db.query(EmployeeClient.client_id).filter(
        EmployeeClient.employee_id == employee_id
    ).all()]

    if not client_ids:
        return [{"client_id": 0, "client_name": "알 수 없음", "total_boxes": 0, "total_sales": 0, "products": []}]

    # ✅ 거래처들의 매출 내역 조회
    sales = (
        db.query(
            SalesRecord.client_id,
            Product.product_name,
            SalesRecord.quantity,
            Product.default_price
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(func.date(SalesRecord.sale_datetime) == sale_date, SalesRecord.client_id.in_(client_ids))
        .all()
    )

    if not sales:
        return [{"client_id": 0, "client_name": "알 수 없음", "total_boxes": 0, "total_sales": 0, "products": []}]

    # ✅ 거래처별 총 매출 및 박스 수 계산
    sales_summary = {}
    for s in sales:
        total_price = (s.default_price or 0) * (s.quantity or 0)
        client_name = client_map.get(s.client_id, "알 수 없음")

        if s.client_id in sales_summary:
            sales_summary[s.client_id]["total_sales"] += total_price
            sales_summary[s.client_id]["total_boxes"] += s.quantity  # ✅ 박스 수 추가
            sales_summary[s.client_id]["products"].append({"product_name": s.product_name, "quantity": s.quantity})
        else:
            sales_summary[s.client_id] = {
                "client_id": s.client_id,
                "client_name": client_name,
                "total_boxes": s.quantity,  # ✅ 박스 수 추가
                "total_sales": total_price,
                "products": [{"product_name": s.product_name, "quantity": s.quantity}]
            }

    print(f"📌 최종 반환 데이터: {list(sales_summary.values())}")   
    return list(sales_summary.values())


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
def list_sales_records(db: Session = Depends(get_db)):
    """ 전체 매출 목록 조회 (KST 그대로 반환) """
    return db.query(SalesRecord).all()  # ✅ 변환 없이 그대로 반환

# -----------------------------------------------------------------------------
# 4. 특정 직원의 매출 조회
# -----------------------------------------------------------------------------
@router.get("/employee/{employee_id}", response_model=List[SalesOut])
def get_sales_by_employee(employee_id: int, db: Session = Depends(get_db)):
    return db.query(SalesRecord).filter(SalesRecord.employee_id == employee_id).all()


# -----------------------------------------------------------------------------
# 5. 특정 날짜의 매출 조회
# -----------------------------------------------------------------------------
@router.get("/date/{sale_date}", response_model=List[SalesOut])
def get_sales_by_date(sale_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 매출 조회 (KST 변환 적용)
    """
    sales = db.query(SalesRecord).filter(
        cast(SalesRecord.sale_datetime, Date) == convert_utc_to_kst(sale_date)  # ✅ KST 변환 적용
    ).all()
    return [convert_sales_to_kst(s) for s in sales]  # ✅ KST 변환 적용


# -----------------------------------------------------------------------------
# 6. 매출 삭제
# -----------------------------------------------------------------------------
@router.delete("/{sales_id}")
def delete_sales_record(sales_id: int, db: Session = Depends(get_db)):
    sales = db.query(SalesRecord).get(sales_id)
    if not sales:
        raise HTTPException(status_code=404, detail="Sales record not found")
    db.delete(sales)
    db.commit()
    return {"detail": "Sales record deleted"}


# -----------------------------------------------------------------------------
# 7. 특정 날짜의 거래처별 판매 품목 목록 반환
# -----------------------------------------------------------------------------
@router.get("/by_client/{sale_date}", response_model=List[SalesOut])
def get_sales_by_client(sale_date: date, db: Session = Depends(get_db)):
    sales = (
        db.query(SalesRecord.client_id, SalesRecord.product_id, Product.product_name, SalesRecord.quantity)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(cast(SalesRecord.sale_datetime, Date) == sale_date)
        .all()
    )
    return [{"client_id": s.client_id, "product_id": s.product_id, "product_name": s.product_name, "quantity": s.quantity} for s in sales]


# -----------------------------------------------------------------------------
# 8. 특정 날짜의 거래처별 총 매출 반환
# -----------------------------------------------------------------------------
@router.get("/sales/total/{sale_date}")
def get_total_sales(sale_date: date, db: Session = Depends(get_db)):
    sales = (
        db.query(SalesRecord.client_id, Product.default_price, SalesRecord.quantity)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(cast(SalesRecord.sale_datetime, Date) == sale_date)
        .all()
    )
    total_sales = {}
    for s in sales:
        total_sales[s.client_id] = total_sales.get(s.client_id, 0) + (s.default_price * s.quantity)
    return [{"client_id": k, "total_sales": v} for k, v in total_sales.items()]


# -----------------------------------------------------------------------------
# 9. 특정 직원 기준, 해당 년도 월별 매출 합계 반환
# -----------------------------------------------------------------------------
@router.get("/monthly_sales_pc/{employee_id}/{year}")
def get_monthly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 직원의 해당 연도 월별 매출 합계 반환 (total_amount 기준)
    """
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(SalesRecord.total_amount).label('sum_sales')
        )
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by('sale_month')
        .all()
    )

    monthly_data = {i + 1: 0 for i in range(12)}
    for row in results:
        m = int(row.sale_month)
        monthly_data[m] = float(row.sum_sales or 0)
    print("📦 반환값 확인:", monthly_data)
    return monthly_data

@router.get("/monthly_sales/{employee_id}/{year}")
def get_yearly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    logger.info(f"📡 Received request: /sales/monthly_sales/{employee_id}/{year}")

    try:
        # ✅ Query yearly sales grouped by client
        results = (
            db.query(
                SalesRecord.client_id,
                Client.client_name,
                func.sum(SalesRecord.quantity).label('total_boxes'),
                func.sum(SalesRecord.return_amount).label('total_refunds'),
                func.sum(Product.default_price * SalesRecord.quantity).label('total_sales')
            )
            .join(Product, SalesRecord.product_id == Product.id)
            .join(Client, SalesRecord.client_id == Client.id)
            .filter(SalesRecord.employee_id == employee_id)
            .filter(extract('year', SalesRecord.sale_datetime) == year)
            .group_by(SalesRecord.client_id, Client.client_name)  # ✅ FIXED: Now grouping by client
            .all()
        )

        logger.info(f"🔍 Raw SQL Query Results: {results}")  # ✅ Log raw data

        # ✅ Convert to list of dictionaries
        sales_data = []
        total_boxes = 0
        total_refunds = 0.0
        total_sales = 0.0

        for idx, row in enumerate(results, start=1):
            sales_data.append({
                "index": idx,  # ✅ 순번 추가
                "client_name": row[1],  # ✅ Korean text preserved
                "total_boxes": int(row[2]) if row[2] else 0,  # ✅ Convert Decimal to int
                "total_refunds": float(row[3]) if row[3] else 0.0,  # ✅ Convert Decimal to float
                "total_sales": float(row[4]) if row[4] else 0.0  # ✅ Convert Decimal to float
            })

            # ✅ Calculate totals for the last row
            total_boxes += int(row[2]) if row[2] else 0
            total_refunds += float(row[3]) if row[3] else 0.0
            total_sales += float(row[4]) if row[4] else 0.0

        # ✅ Add final row for totals (합계)
        if sales_data:
            sales_data.append({
                "index": "합계",
                "client_name": "합계",  # ✅ Korean text for "Total"
                "total_boxes": total_boxes,
                "total_refunds": total_refunds,
                "total_sales": total_sales
            })

        logger.info(f"✅ Formatted Sales Data: {sales_data}")  # ✅ Log formatted data

        return sales_data  # ✅ Return correctly formatted response

    except Exception as e:
        logger.error(f"❌ Error fetching yearly sales for employee {employee_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# -----------------------------------------------------------------------------
# 10. 특정 직원 기준, 해당 년도-월의 일자별 매출 합계 반환
# -----------------------------------------------------------------------------
@router.get("/daily_sales_pc/{employee_id}/{year}/{month}")
def get_daily_sales(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 직원의 해당 연/월의 일별 매출 합계 (total_amount 기준)
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    daily_data = [0.0] * 31

    results = (
        db.query(
            extract('day', SalesRecord.sale_datetime).label('sale_day'),
            func.sum(SalesRecord.total_amount).label('sum_sales')
        )
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .filter(extract('month', SalesRecord.sale_datetime) == month)
        .group_by('sale_day')
        .all()
    )

    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales or 0)

    return daily_data

@router.get("/daily_sales/{employee_id}/{year}/{month}")
def get_daily_sales(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    logger.info(f"📡 Received request: /sales/daily_sales/{employee_id}/{year}/{month}")

    try:
        results = (
            db.query(
                extract('day', SalesRecord.sale_datetime).label('sale_day'),
                SalesRecord.client_id,
                Client.client_name,
                func.sum(SalesRecord.quantity).label('total_boxes'),
                func.sum(SalesRecord.total_amount).label('total_sales')  # ✅ 핵심 변경
            )
            .join(Client, SalesRecord.client_id == Client.id)
            .filter(SalesRecord.employee_id == employee_id)
            .filter(extract('year', SalesRecord.sale_datetime) == year)
            .filter(extract('month', SalesRecord.sale_datetime) == month)
            .group_by(SalesRecord.client_id, Client.client_name, extract('day', SalesRecord.sale_datetime))
            .all()
        )

        sales_data = {}
        for row in results:
            client_id = row.client_id
            day = str(row.sale_day)

            if client_id not in sales_data:
                sales_data[client_id] = {
                    "client_id": client_id,
                    "client_name": row.client_name,
                    "total_boxes": 0,
                    "total_sales": 0,
                }

            sales_data[client_id][day] = float(row.total_sales or 0)
            sales_data[client_id]["total_boxes"] += int(row.total_boxes or 0)
            sales_data[client_id]["total_sales"] += float(row.total_sales or 0)

            print(f"🔍 Processed Sales Data: {sales_data}")

        return JSONResponse(
            content=json.loads(
                json.dumps(list(sales_data.values()), ensure_ascii=False, default=decimal_to_float)
            )
        )

    except Exception as e:
        logger.error(f"❌ Error fetching sales for employee {employee_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

# -----------------------------------------------------------------------------
# 11. 기간별 직원별 총 매출 조회 (직원별 합계)
# -----------------------------------------------------------------------------
@router.get("/sales/employees", response_model=List[dict])
def get_employee_sales(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    query = db.query(
        Sales.employee_id,
        Employee.name.label("employee_name"),
        db.func.sum(Sales.amount).label("total_sales")
    ).join(Employee, Sales.employee_id == Employee.id).group_by(SalesRecordCreate.employee_id)
    
    if start_date:
        query = query.filter(Sales.date >= start_date)
    if end_date:
        query = query.filter(Sales.date <= end_date)
    
    employee_sales = query.all()
    return [
        {
            "employee_id": sale.employee_id,
            "employee_name": sale.employee_name,
            "total_sales": sale.total_sales
        }
        for sale in employee_sales
    ]


# -----------------------------------------------------------------------------
# 12. 기간별 전체 매출 조회 (일자별)
# -----------------------------------------------------------------------------
@router.get("/sales/total", response_model=List[dict])
def get_total_sales(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    from sqlalchemy import func

    query = db.query(
        Sales.date,  # 날짜 기준 그룹핑
        func.sum(Sales.amount).label("total_sales")  # ✅ amount == total_amount 라면 OK
    )

    if start_date:
        query = query.filter(Sales.date >= start_date)
    if end_date:
        query = query.filter(Sales.date <= end_date)

    query = query.group_by(Sales.date).order_by(Sales.date)

    total_sales = query.all()

    return [
        {
            "date": row.date.strftime("%Y-%m-%d"),
            "total_sales": float(row.total_sales or 0)
        }
        for row in total_sales
    ]


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
        new_sale = SalesRecord(
            employee_id=sale_data.employee_id,
            client_id=sale_data.client_id,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            total_amount=total_amount,  # ✅ 총 매출 금액 저장
            sale_datetime=sale_datetime_kst,
            return_amount=sale_data.return_amount,
            subsidy_amount=0.0
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
@router.post("/sales/aggregate")
def create_aggregate_sales(payload: SalesAggregateCreate, db: Session = Depends(get_db)):
    # 1) 요청받은 items에서 product_id별 상품 정보 조회
    product_ids = [item.product_id for item in payload.items]
    products_map = (
        db.query(Product)
          .filter(Product.id.in_(product_ids))
          .all()
    )
    product_dict = {}
    for p in products_map:
        product_dict[p.id] = {
            "category": p.category or "기타",
            "price": float(p.default_price),
        }
    
    # 2) 카테고리별 집계
    category_summary = {}
    for item in payload.items:
        if item.product_id not in product_dict:
            raise HTTPException(status_code=404, detail=f"상품ID={item.product_id} 없음")
        cat  = product_dict[item.product_id]["category"]
        unit = product_dict[item.product_id]["price"]
        subtotal = unit * item.quantity
        if cat not in category_summary:
            category_summary[cat] = {"qty": 0, "amount": 0.0}
        category_summary[cat]["qty"]    += item.quantity
        category_summary[cat]["amount"] += subtotal
    
    # 3) sale_datetime 처리
    sale_dt = payload.sale_datetime or datetime.utcnow()
    
    # 4) 카테고리별 Sales 테이블에 insert
    results = []
    for cat, vals in category_summary.items():
        new_sales = Sales(
            employee_id     = payload.employee_id,
            client_id       = payload.client_id,
            category        = cat,
            total_quantity  = vals["qty"],
            total_amount    = vals["amount"],
            sale_datetime   = sale_dt,
        )
        db.add(new_sales)
        results.append(new_sales)
    
    db.commit()
    for r in results:
        db.refresh(r)
    
    return {
        "detail": "카테고리별 집계 판매 등록 완료",
        "data": [
            {
                "category": r.category,
                "total_quantity": r.total_quantity,
                "total_amount": r.total_amount,
                "sale_datetime": r.sale_datetime,
            }
            for r in results
        ]
    }


# -----------------------------------------------------------------------------
# 16. 특정 거래처 기준, 해당 연도의 월별 매출 합계 반환
# -----------------------------------------------------------------------------
@router.get("/monthly_sales_client/{client_id}/{year}")
def get_monthly_sales_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 거래처의 연도별 월간 매출 합계 (total_amount 기준)
    """
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(SalesRecord.total_amount).label('sum_sales')
        )
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by('sale_month')
        .all()
    )

    monthly_data = [0.0] * 12
    for row in results:
        m = int(row.sale_month) - 1
        monthly_data[m] = float(row.sum_sales or 0)

    return monthly_data


# -----------------------------------------------------------------------------
# 17. 특정 거래처 기준, 해당 연도의 일자별 매출 합계 반환
# -----------------------------------------------------------------------------
@router.get("/daily_sales_client/{client_id}/{year}/{month}")
def get_daily_sales_by_client(client_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 거래처의 해당 연/월 일별 매출 합계 (total_amount 기준)
    """
    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord

    daily_data = [0.0] * 31

    results = (
        db.query(
            extract('day', SalesRecord.sale_datetime).label('sale_day'),
            func.sum(SalesRecord.total_amount).label('sum_sales')
        )
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .filter(extract('month', SalesRecord.sale_datetime) == month)
        .group_by('sale_day')
        .all()
    )

    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales or 0)

    return daily_data

# -----------------------------------------------------------------------------
# 18. '오늘' 날짜 기준, 특정 거래처의 상품 카테고리별 집계 반환
# -----------------------------------------------------------------------------
@router.get("/today_categories_client/{client_id}")
def get_today_categories_for_client(client_id: int, db: Session = Depends(get_db)):
    """
    '오늘' 날짜 기준, 특정 거래처의 상품 카테고리별 집계 반환
    """
    today_kst = get_kst_today()
    start_of_day = datetime.combine(today_kst, datetime.min.time())
    end_of_day = datetime.combine(today_kst, datetime.max.time())

    results = (
        db.query(
            Product.category.label('category'),
            func.sum(SalesRecord.total_amount).label('total_amount'),
            func.sum(SalesRecord.quantity).label('total_qty'),
            Employee.name.label('employee_name')
        )
        .join(SalesRecord, SalesRecord.product_id == Product.id)
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
        .filter(SalesRecord.client_id == client_id)
        .filter(SalesRecord.sale_datetime.between(start_of_day, end_of_day))
        .group_by(Product.category, Employee.name)
        .all()
    )

    data = []
    for row in results:
        data.append({
            "category": row.category or "기타",
            "total_amount": float(row.total_amount or 0),
            "total_qty": int(row.total_qty or 0),
            "employee_name": row.employee_name or "",
        })

    print(f"📌 오늘 카테고리별 판매 데이터: {data}")
    return data


# -----------------------------------------------------------------------------
# 19. 기간별 직원별 매출 조회 (SalesRecord 기준)
# -----------------------------------------------------------------------------
@router.get("/employees_records", response_model=List[dict])
def get_employee_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    from sqlalchemy import func
    query = (
        db.query(
            SalesRecord.employee_id,
            Employee.name.label("employee_name"),
            func.sum(SalesRecord.total_amount).label("total_sales")  # ✅ 핵심 수정
        )
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
    )

    if start_date:
        query = query.filter(SalesRecord.sale_datetime >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_datetime <= end_date)

    query = query.group_by(SalesRecord.employee_id, Employee.name)

    rows = query.all()
    output = []
    for row in rows:
        emp_id, emp_name, total_sales = row
        output.append({
            "employee_id": emp_id or 0,
            "employee_name": emp_name or "미배정",
            "total_sales": float(total_sales or 0)
        })

    return output



# -----------------------------------------------------------------------------
# 20. 기간별 전체 매출 조회 (일자별)
# -----------------------------------------------------------------------------
@router.get("/total_records", response_model=List[dict])
def get_total_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    from sqlalchemy import func
    query = (
        db.query(
            SalesRecord.sale_datetime,
            func.sum(SalesRecord.total_amount).label("total_sales")  # ✅ 핵심 수정
        )
    )

    if start_date:
        query = query.filter(SalesRecord.sale_datetime >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_datetime <= end_date)

    query = query.group_by(SalesRecord.sale_datetime).order_by(SalesRecord.sale_datetime)

    rows = query.all()
    output = []
    for row in rows:
        sale_dt, total_amt = row
        output.append({
            "date": sale_dt.strftime("%Y-%m-%d"),
            "total_sales": float(total_amt or 0)
        })

    return output


# -----------------------------------------------------------------------------
# 21. 기간별 거래처 매출 조회 (거래처별 합계)
# -----------------------------------------------------------------------------
@router.get("/by_client_range", response_model=List[dict])
def get_sales_by_client_range(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    from sqlalchemy import func

    query = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            func.sum(SalesRecord.total_amount).label("total_sales")  # ✅ 핵심 수정
        )
        .join(Client, SalesRecord.client_id == Client.id)
    )

    if start_date:
        query = query.filter(SalesRecord.sale_datetime >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_datetime <= end_date)

    query = query.group_by(SalesRecord.client_id, Client.client_name)

    results = query.all()
    output = []
    for c_id, c_name, sum_amt in results:
        output.append({
            "client_id": c_id,
            "client_name": c_name,
            "total_sales": float(sum_amt or 0)
        })

    return output



# -----------------------------------------------------------------------------
# 22. 특정 연도/월의 세금계산서(매출) 목록 반환
# -----------------------------------------------------------------------------
@router.get("/clients/{year}/{month}")
def get_clients_invoices(year: int, month: int, db: Session = Depends(get_db)):
    import calendar
    from datetime import date
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord
    from app.models.clients import Client

    # 날짜 범위 계산
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # 쿼리: total_amount 사용
    query = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            Client.representative_name.label("client_ceo"),
            Client.business_number,
            func.sum(SalesRecord.total_amount).label("total_sales")  # ✅ 핵심 수정
        )
        .join(Client, SalesRecord.client_id == Client.id)
        .filter(SalesRecord.sale_datetime >= start_date)
        .filter(SalesRecord.sale_datetime <= end_date)
        .group_by(SalesRecord.client_id, Client.client_name, Client.address)
    )

    results = query.all()

    # 반환 형태: 세금계산서 스타일
    data = []
    for row in results:
        total = float(row.total_sales or 0)
        vat = round(total * 0.1, 2)  # ✅ VAT 계산도 정밀하게
        data.append({
            "supplier_id": "",
            "supplier_name": "",
            "supplier_ceo": "",
            "client_id": str(row.client_id),
            "client_name": row.client_name,
            "client_ceo": row.client_ceo,
            "business_number": row.business_number,
            "total_sales": total,
            "tax_amount": vat
        })

    return data


@router.get("/employee_sales/{employee_id}/{year}/{month}")
def get_employee_sales_data(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    직원 기준 해당 월의 거래처 매출 데이터 조회 (MariaDB 호환)
    """
    # 🔹 해당 직원이 담당하는 거래처 목록 가져오기
    client_ids = [c[0] for c in db.query(EmployeeClient.client_id)
                  .filter(EmployeeClient.employee_id == employee_id).all()]
    if not client_ids:
        return []

    # 🔹 현재 월 매출 조회
    current_month_sales = db.query(SalesRecord.client_id, func.sum(SalesRecord.quantity * Product.default_price).label("total_sales"))\
        .join(Product, SalesRecord.product_id == Product.id)\
        .filter(SalesRecord.client_id.in_(client_ids),
                extract('year', SalesRecord.sale_datetime) == year,
                extract('month', SalesRecord.sale_datetime) == month)\
        .group_by(SalesRecord.client_id)\
        .all()

    # 🔹 전월 매출 조회
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_month_sales = db.query(SalesRecord.client_id, func.sum(SalesRecord.quantity * Product.default_price).label("total_sales"))\
        .join(Product, SalesRecord.product_id == Product.id)\
        .filter(SalesRecord.client_id.in_(client_ids),
                extract('year', SalesRecord.sale_datetime) == prev_year,
                extract('month', SalesRecord.sale_datetime) == prev_month)\
        .group_by(SalesRecord.client_id)\
        .all()

    # 🔹 전년도 같은 달 매출 조회
    last_year_sales = db.query(SalesRecord.client_id, func.sum(SalesRecord.quantity * Product.default_price).label("total_sales"))\
        .join(Product, SalesRecord.product_id == Product.id)\
        .filter(SalesRecord.client_id.in_(client_ids),
                extract('year', SalesRecord.sale_datetime) == year - 1,
                extract('month', SalesRecord.sale_datetime) == month)\
        .group_by(SalesRecord.client_id)\
        .all()

    # 🔹 방문 주기 평균 계산 (Python에서 직접 계산)
    visit_frequencies = {}
    for client_id in client_ids:
        visits = db.query(ClientVisit.visit_datetime)\
            .filter(ClientVisit.client_id == client_id)\
            .order_by(ClientVisit.visit_datetime)\
            .all()

        if len(visits) > 1:
            intervals = [(visits[i].visit_datetime - visits[i - 1].visit_datetime).days for i in range(1, len(visits))]
            avg_visit_frequency = sum(intervals) / len(intervals)
        else:
            avg_visit_frequency = 0  # 방문이 1회 이하라면 0 처리

        visit_frequencies[client_id] = avg_visit_frequency

    # 🔹 결과 데이터 정리
    results = []
    for client_id in client_ids:
        results.append({
            "client_id": client_id,
            "client_name": db.query(Client.client_name).filter(Client.id == client_id).scalar(),
            "prev_month_sales": next((s[1] for s in prev_month_sales if s[0] == client_id), 0),
            "last_year_sales": next((s[1] for s in last_year_sales if s[0] == client_id), 0),
            "current_month_sales": next((s[1] for s in current_month_sales if s[0] == client_id), 0),
            "visit_frequency": visit_frequencies.get(client_id, 0)
        })
    
    return results

@router.get("/monthly_sales")
def fetch_monthly_sales(db: Session = Depends(get_db)):
    """
    모든 직원의 이번 달 판매 총합 조회
    """
    today = get_kst_today()
    current_year = today.year
    current_month = today.month

    print(f"📌 [FastAPI] 매출 데이터 요청 - {current_year}년 {current_month}월")

    # 🔹 직원별 매출 합계 계산
    results = (
        db.query(
            SalesRecord.employee_id,
            Employee.name.label("employee_name"),
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Employee, SalesRecord.employee_id == Employee.id)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(extract('year', SalesRecord.sale_datetime) == current_year)
        .filter(extract('month', SalesRecord.sale_datetime) == current_month)
        .group_by(SalesRecord.employee_id, Employee.name)
        .all()
    )

    if not results:
        print("⚠️ [FastAPI] 이번 달 매출 데이터가 없습니다.")

    # 🔹 결과 데이터 변환
    sales_data = [
        {
            "employee_id": row.employee_id,
            "employee_name": row.employee_name,
            "total_sales": float(row.total_sales or 0)
        }
        for row in results
    ]

    print(f"📊 [FastAPI] 매출 데이터 반환: {sales_data}")

    return sales_data


@router.get("/outstanding/{employee_id}")
def get_outstanding_balances(employee_id: int, db: Session = Depends(get_db)):
    results = (
        db.query(Client.client_name, Client.outstanding_amount)
        .join(EmployeeClient, EmployeeClient.client_id == Client.id)
        .filter(EmployeeClient.employee_id == employee_id)
        .all()
    )

    response_data = [
        {"client_name": r.client_name.strip(), "outstanding": float(r.outstanding_amount)}
        for r in results
    ]

    return JSONResponse(content=response_data, media_type="application/json; charset=utf-8")

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


# sales.py (예: 이 파일 제일 아래쪽 등에 추가)
@router.get("/client_monthly_sales")
def get_client_monthly_sales(
    client_id: int = Query(...),
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    특정 거래처(client_id)의 year년도 month월 매출 합계를 반환.
    반환 예시: { "total_sales": 12345.0 }
    """

    from sqlalchemy import extract, func
    from app.models.sales_records import SalesRecord
    from app.models.products import Product

    # 1) 기본 가격 * 수량 = 매출
    sum_val = db.query(
        func.sum(Product.default_price * SalesRecord.quantity)
    )\
    .join(Product, Product.id == SalesRecord.product_id)\
    .filter(SalesRecord.client_id == client_id)\
    .filter(extract('year', SalesRecord.sale_datetime) == year)\
    .filter(extract('month', SalesRecord.sale_datetime) == month)\
    .scalar()

    total_sales = float(sum_val or 0.0)
    return { "total_sales": total_sales }

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
