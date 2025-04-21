# utils/purchase_table_utils.py (또는 app/routers/purchases.py 내)
from functools import lru_cache
from sqlalchemy import Table
from app.db.base import Base, engine
from sqlalchemy.schema import MetaData
from datetime import datetime
from sqlalchemy.exc import NoSuchTableError
from fastapi import HTTPException

metadata = Base.metadata

@lru_cache(maxsize=None)
def get_purchase_model(year: int):
    from app.models.purchases import Purchase
    print(f"🔍 get_purchase_model() 호출됨 with year={year}")
    current_year = datetime.now().year
    if year == current_year:
        return Purchase

    table_name = f"purchases_{year}"

    if table_name in Base.registry._class_registry:
        return Base.registry._class_registry[table_name]

    try:
        tbl = Table(table_name, metadata, autoload_with=engine)
    except NoSuchTableError:
        raise HTTPException(status_code=404, detail=f"테이블 {table_name}이 존재하지 않습니다.")

    model = type(
        f"Purchase{year}",
        (Base,),
        {"__table__": tbl, "__tablename__": table_name}
    )
    return model
