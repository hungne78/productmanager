from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from app.db.database import get_db
from app.models.sales_records import SalesRecord
from app.models.products import Product
from app.models.employee_clients import EmployeeClient
from app.schemas.sales import EmployeeClientSalesOut, SalesRecordCreate, SalesRecordOut, SalesOut
from typing import List
from app.models.sales import Sales
from app.models.employees import Employee
from app.routers.auth import get_current_user  # ✅ 인증 미들웨어 추가
from app.schemas.employees import EmployeeOut
from app.models.clients import Client
from app.schemas.sales import OutstandingUpdate
from app.models.client_visits import ClientVisit
from datetime import datetime
from app.schemas.sales import SalesAggregateCreate, SaleItem
router = APIRouter()

# ✅ 특정 직원이 담당하는 거래처들의 매출 조회
@router.get("/by_employee/{employee_id}/{sale_date}", response_model=List[EmployeeClientSalesOut])
def get_sales_by_employee(employee_id: int, sale_date: date, db: Session = Depends(get_db)):
    """
    특정 직원이 담당하는 거래처들의 매출 데이터 조회
    """
    # 직원이 담당하는 거래처 리스트 가져오기
    client_ids = [c[0] for c in db.query(EmployeeClient.client_id).filter(
        EmployeeClient.employee_id == employee_id
    ).all()]

    if not client_ids:
        print(f"⚠️ 직원 {employee_id}는 거래처가 없습니다.")  # 디버깅 로그 추가
        return []  # ✅ 거래처가 없으면 빈 리스트 반환

    # 해당 직원이 담당하는 거래처들의 매출 내역 조회
    sales = (
        db.query(
            SalesRecord.client_id,
            Product.product_name,
            SalesRecord.quantity,
            Product.default_price,
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.sale_date == sale_date, SalesRecord.client_id.in_(client_ids))
        .all()
    )

    if not sales:
        print(f"⚠️ 직원 {employee_id}의 거래처에 대한 {sale_date} 매출 데이터가 없습니다.")  # 디버깅 로그 추가
        return []  # ✅ 판매 데이터가 없으면 빈 리스트 반환

    # 거래처별 총매출 계산
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

    return list(sales_summary.values())  # ✅ 판매 기록이 있을 경우 반환



@router.post("", response_model=SalesRecordOut)
def create_sales_record(payload: SalesRecordCreate, db: Session = Depends(get_db)):
    """
    새로운 매출 데이터 추가 (단가 자동 계산)
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    total_price = product.default_price * payload.quantity

    # ✅ 직원 방문 기록 업데이트 (같은 날 중복 방문 방지)
    employee_client = db.query(EmployeeClient).filter(
        EmployeeClient.employee_id == payload.employee_id,
        EmployeeClient.client_id == payload.client_id
    ).first()

    if not employee_client:
        new_employee_client = EmployeeClient(
            employee_id=payload.employee_id,
            client_id=payload.client_id,
            visit_count=1  # ✅ 첫 방문
        )
        db.add(new_employee_client)

    # ✅ 방문 기록 확인 (하루에 한 번만 방문 횟수 증가)
    visit = db.query(ClientVisit).filter(
        ClientVisit.employee_id == payload.employee_id,
        ClientVisit.client_id == payload.client_id,
        ClientVisit.visit_datetime == payload.sale_date  # ✅ 올바른 필드명 사용
    ).first()

    if not visit:
        new_visit = ClientVisit(
            employee_id=payload.employee_id,
            client_id=payload.client_id,
            visit_datetime=payload.sale_date  # ✅ 올바른 필드 사용
        )
        db.add(new_visit)

    # ✅ 매출 데이터 저장
    new_sales = SalesRecord(
        employee_id=payload.employee_id,
        client_id=payload.client_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        sale_date=payload.sale_date
    )

    db.add(new_sales)
    db.commit()
    db.refresh(new_sales)

    return {
        "id": new_sales.id,
        "employee_id": new_sales.employee_id,
        "client_id": new_sales.client_id,
        "product_id": new_sales.product_id,
        "product_name": product.product_name,
        "quantity": new_sales.quantity,
        "unit_price": float(product.default_price),
        "total_amount": float(total_price),
        "sale_date": new_sales.sale_date
    }


# ✅ 전체 매출 목록 조회
@router.get("/", response_model=List[SalesOut])
def list_sales_records(db: Session = Depends(get_db)):
    return db.query(SalesRecord).all()

# ✅ 특정 직원의 매출 조회
@router.get("/employee/{employee_id}", response_model=List[SalesOut])
def get_sales_by_employee(employee_id: int, db: Session = Depends(get_db)):
    return db.query(SalesRecord).filter(SalesRecord.employee_id == employee_id).all()

# ✅ 특정 날짜의 매출 조회
@router.get("/date/{sale_date}", response_model=List[SalesOut])
def get_sales_by_date(sale_date: date, db: Session = Depends(get_db)):
    return db.query(SalesRecord).filter(SalesRecord.sale_date == sale_date).all()

# ✅ 매출 삭제
@router.delete("/{sales_id}")
def delete_sales_record(sales_id: int, db: Session = Depends(get_db)):
    sales = db.query(SalesRecord).get(sales_id)
    if not sales:
        raise HTTPException(status_code=404, detail="Sales record not found")
    db.delete(sales)
    db.commit()
    return {"detail": "Sales record deleted"}

@router.get("/by_client/{sale_date}", response_model=List[SalesOut])
def get_sales_by_client(sale_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 거래처별 판매 품목 목록 반환
    """
    sales = (
        db.query(SalesRecord.client_id, SalesRecord.product_id, Product.product_name, SalesRecord.quantity)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.sale_date == sale_date)
        .all()
    )

    return [{"client_id": s.client_id, "product_id": s.product_id, "product_name": s.product_name, "quantity": s.quantity} for s in sales]

@router.get("/sales/total/{sale_date}")
def get_total_sales(sale_date: date, db: Session = Depends(get_db)):
    """
    특정 날짜의 거래처별 총 매출 반환
    """
    sales = (
        db.query(SalesRecord.client_id, Product.default_price, SalesRecord.quantity)
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.sale_date == sale_date)
        .all()
    )

    total_sales = {}
    for s in sales:
        total_sales[s.client_id] = total_sales.get(s.client_id, 0) + (s.default_price * s.quantity)

    return [{"client_id": k, "total_sales": v} for k, v in total_sales.items()]

@router.get("/monthly_sales/{employee_id}/{year}")
def get_monthly_sales(employee_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 직원 기준, 해당 년도(year)의 월별 매출 합계를 1~12월 순으로 리턴
    리턴 예시: [100, 200, 300, ... 12개]
    """
    from sqlalchemy import extract, func

    results = (
        db.query(
            extract('month', SalesRecord.sale_date).label('sale_month'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_date) == year)
        .group_by(extract('month', SalesRecord.sale_date))
        .all()
    )

    # 월별 누락된 달은 0으로 채워 넣기
    monthly_data = [0]*12
    for row in results:
        m = int(row.sale_month) - 1  # 1월이면 index=0
        monthly_data[m] = float(row.sum_sales)

    return monthly_data

@router.get("/daily_sales/{employee_id}/{year}/{month}")
def get_daily_sales(employee_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 직원 기준, year년 month월의 일자별 매출 합계 (1일부터 31일까지)
    예: [0, 20, 0, 50, ...] 31개 (해당 달의 최대 일수만큼)
    """
    from sqlalchemy import extract, func

    # 31일까지 만들어두고, 실제 값이 있으면 덮어씀
    daily_data = [0]*31

    results = (
        db.query(
            extract('day', SalesRecord.sale_date).label('sale_day'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.employee_id == employee_id)
        .filter(extract('year', SalesRecord.sale_date) == year)
        .filter(extract('month', SalesRecord.sale_date) == month)
        .group_by(extract('day', SalesRecord.sale_date))
        .all()
    )

    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales)

    return daily_data

@router.get("/sales/employees", response_model=List[dict])
def get_employee_sales(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    """
    기간별 직원별 총 매출 조회
    """
    query = db.query(
        Sales.employee_id,
        Employee.name.label("employee_name"),
        db.func.sum(Sales.amount).label("total_sales")
    ).join(Employee, Sales.employee_id == Employee.id).group_by(SalesRecordCreate.employee_id)

    # ✅ 날짜 필터링 추가
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


@router.get("/sales/total", response_model=List[dict])
def get_total_sales(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    """
    기간별 전체 매출 조회
    """
    query = db.query(
        Sales.date,
        db.func.sum(Sales.amount).label("total_sales")
    ).group_by(Sales.date)

    # ✅ 날짜 필터링 추가
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
    
@router.post("/sales", response_model=SalesRecordOut)
def create_sale(sale_data: SalesRecordCreate, db: Session = Depends(get_db)):
    """
    판매 데이터 등록 API
    """
    print(f"📡 판매 등록 요청 데이터: {sale_data.dict()}")  

    try:
        product = db.query(Product).filter(Product.id == sale_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

        # ✅ 재고 차감
        if product.stock < sale_data.quantity:
            raise HTTPException(status_code=400, detail="재고 부족")

        product.stock -= sale_data.quantity

        # ✅ 총 판매 금액 계산
        total_amount = sale_data.quantity * product.default_price

        # ✅ 판매 데이터 저장
        new_sale = Sales(
            employee_id=sale_data.employee_id,
            client_id=sale_data.client_id,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            unit_price=product.default_price,
            total_amount=total_amount,
            sale_date=sale_data.sale_date
        )

        db.add(new_sale)
        db.commit()
        db.refresh(new_sale)

        return new_sale

    except Exception as e:
        db.rollback()
        print(f"❌ 판매 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"판매 등록 실패: {e}")
    
@router.put("/outstanding/{client_id}")
def update_outstanding(
    client_id: int,
    update_data: OutstandingUpdate,  # ✅ 요청 바디를 Pydantic 모델로 받음
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

    client.outstanding_amount = update_data.outstanding_amount  # ✅ 올바른 데이터 저장
    db.commit()
    
    print(f"✅ 미수금 업데이트 성공: 클라이언트 {client_id}, 새로운 미수금 {update_data.outstanding_amount}")

    return {"detail": "Outstanding amount updated successfully"}

@router.post("/sales/aggregate")
def create_aggregate_sales(payload: SalesAggregateCreate, db: Session = Depends(get_db)):
    """
    여러 상품을 한 번에 판매등록 -> 카테고리별로 합산하여 sales 테이블에 기록
    """
    # 1) 요청으로 받은 items 에서 product_id별로 상품 정보 조회
    product_ids = [item.product_id for item in payload.items]
    products_map = (
        db.query(Product)
          .filter(Product.id.in_(product_ids))
          .all()
    )
    # products_map을 { product_id: (category, default_price) } 형태 등으로 만들기
    product_dict = {}
    for p in products_map:
        product_dict[p.id] = {
            "category": p.category or "기타",
            "price": float(p.default_price),  # decimal → float
        }

    # 2) 카테고리별로 집계하기
    #    예: {"바": {"qty": 3, "amount": 4500}, "콘": {"qty": 2, "amount": 3000}, ...}
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

    # 4) 카테고리별로 Sales 테이블에 insert
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

    # 🎉 DB 반영 후, 각 row refresh
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
# 예: app/routers/sales.py 하단에 추가

from sqlalchemy import extract, func
from datetime import date

@router.get("/monthly_sales_client/{client_id}/{year}")
def get_monthly_sales_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 '거래처(client_id)' 기준, 해당 연도(year)의 월별 매출 합계를 1~12월 순으로 리턴
    예: [100, 200, 300, ... 12개]
    """
    results = (
        db.query(
            extract('month', SalesRecord.sale_date).label('sale_month'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_date) == year)
        .group_by(extract('month', SalesRecord.sale_date))
        .all()
    )

    monthly_data = [0]*12
    for row in results:
        m = int(row.sale_month) - 1
        monthly_data[m] = float(row.sum_sales or 0)
    return monthly_data


@router.get("/monthly_visits_client/{client_id}/{year}")
def get_monthly_visits_by_client(client_id: int, year: int, db: Session = Depends(get_db)):
    """
    특정 '거래처(client_id)' 기준, 해당 연도(year)의 월별 방문 횟수 (client_visits 테이블 기반)
    예: [3, 5, 2, ... 12개]
    """
    results = (
        db.query(
            extract('month', ClientVisit.visit_datetime).label('visit_month'),
            func.count(ClientVisit.id).label('cnt')
        )
        .filter(ClientVisit.client_id == client_id)
        .filter(extract('year', ClientVisit.visit_datetime) == year)
        .group_by(extract('month', ClientVisit.visit_datetime))
        .all()
    )

    monthly_counts = [0]*12
    for row in results:
        m = int(row.visit_month) - 1
        monthly_counts[m] = int(row.cnt or 0)
    return monthly_counts


@router.get("/daily_sales_client/{client_id}/{year}/{month}")
def get_daily_sales_by_client(client_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """
    특정 '거래처(client_id)' 기준, year년 month월의 일자별 매출 합계
    예: [0, 20, 0, 50, ...] 최대 31개
    """
    daily_data = [0]*31

    results = (
        db.query(
            extract('day', SalesRecord.sale_date).label('sale_day'),
            func.sum(Product.default_price * SalesRecord.quantity).label('sum_sales')
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .filter(SalesRecord.client_id == client_id)
        .filter(extract('year', SalesRecord.sale_date) == year)
        .filter(extract('month', SalesRecord.sale_date) == month)
        .group_by(extract('day', SalesRecord.sale_date))
        .all()
    )

    for row in results:
        d = int(row.sale_day) - 1
        daily_data[d] = float(row.sum_sales or 0)

    return daily_data


@router.get("/today_categories_client/{client_id}")
def get_today_categories_for_client(client_id: int, db: Session = Depends(get_db)):
    """
    '오늘 날짜(date.today() 기준)'에 거래처(client_id)에 대해
    상품 category별 판매금액/수량/직원명 등을 집계하여 리턴
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
        .filter(SalesRecord.sale_date == today)
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
@router.get("/employees_records", response_model=List[dict])
def get_employee_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    """
    SalesRecord 테이블을 기준으로 기간별 직원별 매출(=Product.default_price * SalesRecord.quantity) 조회
    """
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

    # 날짜 필터
    if start_date:
        query = query.filter(SalesRecord.sale_date >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_date <= end_date)

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


@router.get("/total_records", response_model=List[dict])
def get_total_sales_records(
    db: Session = Depends(get_db),
    start_date: date = Query(None),
    end_date: date = Query(None)
):
    """
    SalesRecord 테이블을 기준으로 기간별 '일자별' 총 매출(=default_price * quantity)
    """
    from sqlalchemy import func
    query = (
        db.query(
            SalesRecord.sale_date,
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Product, SalesRecord.product_id == Product.id, isouter=True)
    )
    # 날짜 필터
    if start_date:
        query = query.filter(SalesRecord.sale_date >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_date <= end_date)

    query = query.group_by(SalesRecord.sale_date).order_by(SalesRecord.sale_date)
    rows = query.all()

    output = []
    for row in rows:
        sale_dt, total_amt = row
        output.append({
            "date": sale_dt.strftime("%Y-%m-%d"),
            "total_sales": float(total_amt or 0)
        })
    return output

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
            Client.client_name,  # ✅ 거래처명도
            func.sum(Product.default_price * SalesRecord.quantity).label("total_sales")
        )
        .join(Product, SalesRecord.product_id == Product.id)
        .join(Client, SalesRecord.client_id == Client.id)   # ✅ 이 부분 꼭 추가!
    )
    if start_date:
        query = query.filter(SalesRecord.sale_date >= start_date)
    if end_date:
        query = query.filter(SalesRecord.sale_date <= end_date)

    # group_by도 SalesRecord.client_id, Client.client_name 둘 다 해야 함
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

