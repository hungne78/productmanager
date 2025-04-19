# utils/franchise_archive_utils.py

from functools import lru_cache
from sqlalchemy import Table
from sqlalchemy.schema import MetaData
from datetime import datetime
from app.db.base import Base, engine

metadata = Base.metadata

@lru_cache(maxsize=None)
def get_franchise_order_model(year: int):
    from app.models.franchise_order import FranchiseOrder  # ✅ 메인 모델 기준

    if year == datetime.now().year:
        return FranchiseOrder  # ✅ 올해는 본 테이블 사용

    table_name = f"franchise_orders_{year}"
    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)
    return type(f"FranchiseOrder{year}", (Base,), {"__table__": tbl, "__tablename__": table_name})


@lru_cache(maxsize=None)
def get_franchise_item_model(year: int):
    from app.models.franchise_order import FranchiseOrderItem

    if year == datetime.now().year:
        return FranchiseOrderItem

    table_name = f"franchise_order_items_{year}"
    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    tbl = Table(table_name, metadata, autoload_with=engine)
    return type(f"FranchiseOrderItem{year}", (Base,), {"__table__": tbl, "__tablename__": table_name})
