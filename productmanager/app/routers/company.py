from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.company import CompanyInfo
from app.schemas.company import CompanySchema

router = APIRouter()

@router.get("/", response_model=CompanySchema)
def get_company_info(db: Session = Depends(get_db)):
    """회사 정보 조회"""
    company = db.query(CompanyInfo).first()
    if not company:
        raise HTTPException(status_code=404, detail="회사 정보가 없습니다.")
    return company

@router.post("/")
def create_or_update_company_info(company_data: CompanySchema, db: Session = Depends(get_db)):
    """회사 정보 생성 또는 업데이트"""
    company = db.query(CompanyInfo).first()

    if company:
        # 기존 데이터 업데이트
        company.company_name = company_data.company_name
        company.ceo_name = company_data.ceo_name
        company.address = company_data.address
        company.phone = company_data.phone
        company.business_number = company_data.business_number
        company.bank_account = company_data.bank_account
    else:
        # 새 데이터 생성
        company = CompanyInfo(**company_data.dict())
        db.add(company)

    db.commit()
    return {"message": "회사 정보가 저장되었습니다."}
