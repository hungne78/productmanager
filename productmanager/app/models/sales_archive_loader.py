def get_sales_model_for_year(year: int):
    from datetime import datetime
    current_year = datetime.now().year

    if year == current_year:
        from app.models.sales_records import SalesRecord
        return SalesRecord
    
    # 동적으로 모듈 import
    try:
        mod = __import__(f"app.models.sales_records_{year}", fromlist=["SalesRecordArchive"])
        return getattr(mod, "SalesRecordArchive")
    except ImportError:
        raise Exception(f"⚠️ {year}년 아카이브 모델을 찾을 수 없습니다.")
