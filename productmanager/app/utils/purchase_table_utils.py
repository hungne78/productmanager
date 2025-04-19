# utils/purchase_table_utils.py (또는 app/routers/purchases.py 내)
from functools import lru_cache
from sqlalchemy import Table
from app.db.base import Base, engine
from sqlalchemy.schema import MetaData
from datetime import datetime

metadata = Base.metadata

@lru_cache(maxsize=None)
def get_purchase_model(year: int):
    """
    현재 연도면 기존 Purchase 모델을 반환하고,
    과거 연도면 purchases_YYYY 테이블을 리플렉션해서 동적 모델 생성
    """
    from app.models.purchases import Purchase  # 순환 import 방지

    current_year = datetime.now().year
    if year == current_year:
        return Purchase

    table_name = f"purchases_{year}"

    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)

    model = type(
        f"Purchase{year}",
        (Base,),
        {"__table__": tbl, "__tablename__": table_name}
    )
    return model
