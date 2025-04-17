from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.archive_service import archive_sales_for_year
from app.db.database import get_db

router = APIRouter(prefix="/admin/archive", tags=["🧾 아카이빙"])

@router.post("/{year}")
def run_sales_archive(year: int, db: Session = Depends(get_db)):
    """
    🔐 특정 연도의 매출 데이터를 아카이브 테이블로 이동
    """
    try:
        archive_sales_for_year(year, db)
        return {"message": f"{year}년 매출 아카이브 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"아카이빙 실패: {e}")
