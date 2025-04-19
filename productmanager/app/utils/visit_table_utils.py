# utils/visit_table_utils.py

from functools import lru_cache
from sqlalchemy import Table
from sqlalchemy.schema import MetaData
from datetime import datetime
from app.db.base import Base, engine

metadata = Base.metadata

@lru_cache(maxsize=None)
def get_visit_model(year: int):
    """
    올해는 기본 ClientVisit 모델,
    과거 연도면 client_visits_YYYY 테이블 리플렉션해서 동적 모델 생성
    """
    from app.models.client_visits import ClientVisit  # 순환 import 방지

    curr_year = datetime.now().year
    if year == curr_year:
        return ClientVisit

    table_name = f"client_visits_{year}"
    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)

    model = type(
        f"ClientVisit{year}",
        (Base,),
        {"__table__": tbl, "__tablename__": table_name}
    )
    return model
