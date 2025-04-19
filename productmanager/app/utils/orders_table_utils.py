# app/utils/orders_table_utils.py
from datetime import datetime
from sqlalchemy import Table, MetaData
from sqlalchemy.orm import declarative_base
from functools import lru_cache
from app.db.database import engine
from app.models.orders import Order, OrderItem          # 원본 모델 import

Base      = declarative_base()
metadata  = MetaData()
CURR_YEAR = datetime.now().year

@lru_cache(maxsize=None)
def get_order_model(year: int):
    """orders_YYYY 테이블 → 동적 모델 생성 (올해면 기존 Order 반환)"""
    if year == CURR_YEAR:
        return Order

    tbl = Table(f"orders_{year}", metadata, autoload_with=engine)
    return type(f"orders_{year}", (Base,), {"__table__": tbl})

@lru_cache(maxsize=None)
def get_order_item_model(year: int):
    """order_items_YYYY 테이블 → 동적 모델 생성 (올해면 기존 OrderItem)"""
    if year == CURR_YEAR:
        return OrderItem

    tbl = Table(f"order_items_{year}", metadata, autoload_with=engine)
    return type(f"order_items_{year}", (Base,), {"__table__": tbl})
