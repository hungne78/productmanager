from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.db.database import get_db
from app.models.sales_records import SalesRecord
from app.models.products import Product
from app.models.employee_clients import EmployeeClient
from app.schemas.sales import EmployeeClientSalesOut, SalesRecordCreate, SalesRecordOut, SalesOut
from typing import List

router = APIRouter()

# ✅ 특정 직원이 담당하는 거래처들의 매출 조회
@router.get("/sales/by_employee/{employee_id}/{sale_date}", response_model=List[EmployeeClientSalesOut])
def get_sales_by_employee(employee_id: int, sale_date: date, db: Session = Depends(get_db)):
    """
    특정 직원이 담당하는 거래처들의 매출 데이터 조회
    """
    # 직원이 담당하는 거래처 리스트 가져오기
    client_ids = db.query(EmployeeClient.client_id).filter(
        EmployeeClient.employee_id == employee_id
    ).all()

    if not client_ids:
        raise HTTPException(status_code=404, detail="해당 직원이 담당하는 거래처가 없습니다.")

    client_ids = [c[0] for c in client_ids]

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
        raise HTTPException(status_code=404, detail="해당 직원의 거래처에 대한 매출 데이터가 없습니다.")

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

    return list(sales_summary.values())


# ✅ 매출 등록 (단가 자동 조회)
@router.post("/sales", response_model=SalesRecordOut)
def create_sales_record(payload: SalesRecordCreate, db: Session = Depends(get_db)):
    """
    새로운 매출 데이터 추가 (단가 자동 계산)
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    total_price = product.default_price * payload.quantity

    new_sales = SalesRecord(
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

@router.get("/sales/by_client/{sale_date}", response_model=List[SalesOut])
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
