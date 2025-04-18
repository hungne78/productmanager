from datetime import datetime
from sqlalchemy import Table, MetaData
from sqlalchemy.orm import declarative_base, mapper
from functools import lru_cache
from app.db.database import engine   # 기존 DB 엔진 재사용

Base = declarative_base()
metadata = MetaData()

@lru_cache(maxsize=None)
def get_sales_model(year: int):
    """
    year 가 올해면 기존 SalesRecord 모델을 돌려주고,
    그렇지 않으면 salesrecord_YYYY 테이블을 리플렉션하여
    즉석에서 SQLAlchemy 모델 클래스를 만들어 반환한다.
    """
    from app.models.sales_records import SalesRecord  # 순환 import 방지

    curr_year = datetime.now().year
    if year == curr_year:
        return SalesRecord

    table_name = f"sales_records_{year}"
    # 이미 캐싱된 모델이 있으면 그대로
    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    # ➊ 테이블 리플렉션
    tbl = Table(table_name, metadata, autoload_with=engine)

    # ➋ 동적 모델 클래스 생성
    model = type(
        f"sales_records_{year}",
        (Base,),
        {"__table__": tbl, "__tablename__": table_name}
    )
    return model
