from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from sqlalchemy import cast, Date, extract, func
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
router = APIRouter()

def convert_sales_to_kst(sale: SalesRecord):
    """
    SalesRecord 객체의 `sale_datetime`을 KST로 변환하여 반환
    """
    sale_dict = {
        "id": sale.id,
        "employee_id": sale.employee_id,
        "client_id": sale.client_id,
        "product_id": sale.product_id,
        "quantity": sale.quantity,
        "sale_datetime": sale.sale_datetime.isoformat() if sale.sale_datetime else None
    }
    return sale_dict
# -----------------------------------------------------------------------------
# 1. 특정 직원이 담당하는 거래처들의 매출 조회
# -----------------------------------------------------------------------------
@router.get("/by_employee/{employee_id}/{sale_date}", response_model=List[EmployeeClientSalesOut])
def get_sales_by_employee(employee_id: int, sale_date: date, db: Session = Depends(get_db)):
    """
    특정 직원이 담당하는 거래처들의 매출 데이터를 조회합니다.
    """
    # 직원이 담당하는 거래처 리스트 가져오기
    client_ids = [c[0] for c in db.query(EmployeeClient.client_id).filter(
        EmployeeClient.employee_id == employee_id
    ).all()]

    if not client_ids:
        print(f"⚠️ 직원 {employee_id}는 거래처가 없습니다.")
        return []  # 거래처가 없으면 빈 리스트 반환

    # 거래처들의 매출 내역 조회 (비교 시 sale_datetime의 날짜 부분만 사용)
    sales = (
        db.query(
            SalesRecord.client_id,
            Product.product_name,
            SalesRecord.quantity,
            Product.default_price,
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(cast(SalesRecord.sale_datetime, Date) == sale_date, SalesRecord.client_id.in_(client_ids))
        .all()
    )

    if not sales:
        print(f"⚠️ 직원 {employee_id}의 거래처에 대한 {sale_date} 매출 데이터가 없습니다.")
        return []

    # 거래처별 총 매출 계산
    sales_summary = {}
    for s in sales:
        total_price = s.default_price * s.quantity
        if s.client_id in sales_summary:
            sales_summary[s.client_id]["total_sales"] += total_price
            sales_summary[s.client_id]["products"].append({"product_name": s.product_name, "quantity": s.quantity})
        else:
            sales_summary[s.client_id] = {
                "client_id": s.client_id,
                "total_sales": total_price,
                "products": [{"product_name": s.product_name, "quantity": s.quantity}]
            }

    return list(sales_summary.values())


# -----------------------------------------------------------------------------
# 2. 새로운 매출 데이터 등록 (단가 자동 계산)
# -----------------------------------------------------------------------------
@router.post("", response_model=SalesRecordOut)
def create_sales_record(payload: SalesRecordCreate, db: Session = Depends(get_db)):
    """
    새로운 매출 데이터를 등록합니다. (KST 적용)
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    total_price = product.default_price * payload.quantity

    new_sales = SalesRecord(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        sale_datetime=payload.sale_datetime if payload.sale_datetime else get_kst_now()  # ✅ KST 적용
    )

    db.add(new_sales)
    db.commit()
    db.refresh(new_sales)

    return convert_sales_to_kst(new_sales)  # ✅ KST 변환 후 반환

# -----------------------------------------------------------------------------
# 3. 전체 매출 목록 조회
# -----------------------------------------------------------------------------
@router.get("/", response_model=List[SalesOut])
def list_sales_records(db: Session = Depends(get_db)):
    """
    전체 매출 목록 조회 (KST 변환 적용)
    """
    sales = db.query(SalesRecord).all()
    return [convert_sales_to_kst(s) for s in sales]  # ✅ KST 변환 적용

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
@router.get("/monthly_sales/{employee_id}/{year}")
def get_monthly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by(extract('month', SalesRecord.sale_datetime))
        .all()
    )
    monthly_data = [0] * 12
    for row in results:
        m = int(row.sale_month) - 1  # 1월이면 index 0
        monthly_data[m] = float(row.sum_sales or 0)
    return monthly_data


# -----------------------------------------------------------------------------
# 10. 특정 직원 기준, 해당 년도-월의 일자별 매출 합계 반환
# -----------------------------------------------------------------------------
@router.get("/daily_sales/{employee_id}/{year}/{month}")
def get_daily_sales(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    daily_data = [0] * 31
    results = (
        db.query(
            extract('day', SalesRecord.sale_datetime).label('sale_day'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .filter(extract('month', SalesRecord.sale_datetime) == month)
        .group_by(extract('day', SalesRecord.sale_datetime))
        .all()
    )
    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales or 0)
    return daily_data


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
    query = db.query(
        Sales.date,
        db.func.sum(Sales.amount).label("total_sales")
    ).group_by(Sales.date)
    
    if start_date:
        query = query.filter(Sales.date >= start_date)
    if end_date:
        query = query.filter(Sales.date <= end_date)
    
    total_sales = query.all()
    return [
        {
            "date": sale.date.strftime("%Y-%m-%d"),
            "total_sales": sale.total_sales
        }
        for sale in total_sales
    ]


# -----------------------------------------------------------------------------
# 13. 판매 데이터 등록 (매출 등록 API)
# -----------------------------------------------------------------------------
@router.post("/sales", response_model=SalesRecordOut)
def create_sale(sale_data: SalesRecordCreate, db: Session = Depends(get_db)):
    print(f"📡 판매 등록 요청 데이터: {sale_data.dict()}")

    try:
        product = db.query(Product).filter(Product.id == sale_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
        
        # 재고 차감
        # product.stock -= sale_data.quantity
        total_amount = sale_data.quantity * product.default_price

        # 매출 기록 저장 (Sales 테이블)
        new_sale = Sales(
            employee_id=sale_data.employee_id,
            client_id=sale_data.client_id,
            product_id=sale_data.product_id,
            total_quantity=sale_data.quantity,
            total_amount=total_amount,
            sale_datetime=sale_data.sale_datetime if sale_data.sale_datetime else get_kst_now()  # ✅ KST 적용
        )
        db.add(new_sale)
        db.flush()  # 즉시 반영

        # SalesRecord 테이블에도 기록이 필요할 수 있음
        new_sales_record = SalesRecord(
            employee_id=sale_data.employee_id,
            client_id=sale_data.client_id,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            sale_datetime=sale_data.sale_datetime if sale_data.sale_datetime else get_kst_now()  # ✅ KST 적용
        )
        db.add(new_sales_record)
        db.flush()  # 즉시 반영
        db.commit()  # 최종 저장
        db.refresh(new_sale)
        db.refresh(new_sales_record)

        print(f"✅ 매출 저장 완료: ID={new_sale.id}, 총액={new_sale.total_amount}")

        return convert_sales_to_kst(new_sale)

    except Exception as e:
        db.rollback()
        print(f"❌ 판매 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"판매 등록 실패: {e}")


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
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by(extract('month', SalesRecord.sale_datetime))
        .all()
    )
    monthly_data = [0] * 12
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
    특정 거래처 기준, 해당 연도의 월별 매출 합계 반환
    """
    daily_data = [0] * 31

    results = (
        db.query(
            extract('day', SalesRecord.sale_datetime).label('sale_day'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .filter(extract('month', SalesRecord.sale_datetime) == month)
        .group_by(extract('day', SalesRecord.sale_datetime))
        .all()
    )

    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales)

    return daily_data


# -----------------------------------------------------------------------------
# 18. '오늘' 날짜 기준, 특정 거래처의 상품 카테고리별 집계 반환
# -----------------------------------------------------------------------------
@router.get("/today_categories_client/{client_id}")
def get_today_categories_for_client(client_id: int, db: Session = Depends(get_db)):
    """
    '오늘' 날짜 기준, 특정 거래처의 상품 카테고리별 집계 반환
    """
    today = date.today()
    results = (
        db.query(
            Product.category.label('category'),
            func.sum(Product.default_price * SalesRecord.quantity).label('total_amount'),
            func.sum(SalesRecord.quantity).label('total_qty'),
            Employee.name.label('employee_name')
        )
        .join(SalesRecord, SalesRecord.product_id == Product.id)
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
        .filter(SalesRecord.client_id == client_id)
        .filter(cast(SalesRecord.sale_datetime, Date) == today)
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
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Employee, SalesRecord.employee_id == Employee.id, isouter=True)
        .join(Product, SalesRecord.product_id == Product.id, isouter=True)
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
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Product, SalesRecord.product_id == Product.id, isouter=True)
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
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Product, SalesRecord.product_id == Product.id)
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
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    from sqlalchemy import func
    from app.models.sales_records import SalesRecord
    from app.models.clients import Client
    from app.models.products import Product
    
    query = (
        db.query(
            SalesRecord.client_id,
            Client.client_name,
            Client.address.label("client_ceo"),
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales"),
        )
        .join(Client, SalesRecord.client_id == Client.id)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.sale_datetime >= start_date)
        .filter(SalesRecord.sale_datetime <= end_date)
        .group_by(SalesRecord.client_id, Client.client_name, Client.address)
    )
    
    results = query.all()
    data = []
    for row in results:
        total = float(row.total_sales or 0)
        vat = total * 0.1
        data.append({
            "supplier_id": "",
            "supplier_name": "",
            "supplier_ceo": "",
            "client_id": str(row.client_id),
            "client_name": row.client_name,
            "client_ceo": row.client_ceo,
            "total_sales": total,
            "tax_amount": vat
        })
    return data

@router.get("/monthly_sales/{employee_id}/{year}")
def get_monthly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 직원의 해당 연도 월별 매출 합계 반환
    """
    results = (
        db.query(
            extract('month', SalesRecord.sale_datetime).label('sale_month'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_datetime) == year)
        .group_by(extract('month', SalesRecord.sale_datetime))
        .all()
    )

    monthly_data = [0] * 12
    for row in results:
        m = int(row.sale_month) - 1  # 1월이면 index=0
        monthly_data[m] = float(row.sum_sales)

    return monthly_data
