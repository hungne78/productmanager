# app/main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import engine, SessionLocal
from app.db.base import Base
from app.routers.employees import router as employees_router
from app.routers.auth import auth_router
from app.routers import employees, clients, products, orders, lent, purchases, sales
from app.routers.employee_clients import router as employee_clients_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.client_visits import router as client_visits_router
from app.routers.employee_vehicle import router as employee_vehicle_router
from app.routers.sales import router as sales_router
from app.routers.brands import router as brands_router
from app.core.security import get_password_hash
from app.routers import payments
from app.models.employees import Employee
from app.routers.employee_map_routers import router as employee_map_router
from app.routers import client_visits
from app.utils.time_utils import convert_utc_to_kst  # ✅ KST 변환 함수 추가
import json

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(Employee).filter(Employee.id == 1).first()
        if not admin:
            hashed_pw = get_password_hash("admin123")
            admin = Employee(
                password_hash=hashed_pw,
                name="심형섭",
                phone="01029683796",
                role="admin"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Default admin created")
    finally:
        db.close()
    yield
    print("Shutdown: Cleaning up...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        redirect_slashes=False,
    )

    # ✅ 미들웨어 추가: FastAPI 응답의 날짜를 자동으로 KST 변환
    @app.middleware("http")
    async def convert_datetime_to_kst(request: Request, call_next):
        response = await call_next(request)
        
        # 응답이 JSON이 아닌 경우(스트리밍 응답) 처리
        if isinstance(response, JSONResponse):
            try:
                content = response.body.decode("utf-8")
                content = json.loads(content)
                # KST 변환
                if isinstance(content, dict):  # dict 형식의 응답 처리
                    content = convert_utc_to_kst_recursive(content)
                elif isinstance(content, list):  # list 형식의 응답 처리
                    content = [convert_utc_to_kst_recursive(item) for item in content]
                response = JSONResponse(content=content)
            except Exception as e:
                print(f"❌ KST 변환 오류: {e}")
        
        return response

    def convert_utc_to_kst_recursive(obj):
        """ 재귀적으로 UTC → KST 변환 """
        if isinstance(obj, dict):
            return {k: convert_utc_to_kst_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_utc_to_kst_recursive(i) for i in obj]
        elif isinstance(obj, str):  # ISO 8601 날짜 문자열 변환
            try:
                from datetime import datetime
                parsed_date = datetime.fromisoformat(obj)
                return convert_utc_to_kst(parsed_date).isoformat()
            except ValueError:
                return obj  # 변환 실패 시 원래 값 반환
        return obj  # 기본값 반환

    # CORS 미들웨어 추가
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    app.include_router(auth_router, prefix="", tags=["Auth"])
    app.include_router(employees.router, prefix="/employees", tags=["Employees"])
    app.include_router(clients.router, prefix="/clients", tags=["Clients"])
    app.include_router(products.router, prefix="/products", tags=["Products"])
    app.include_router(orders.router, prefix="/orders", tags=["Orders"])
    app.include_router(employee_clients_router, prefix="/employee_clients", tags=["Employee-Client"])
    app.include_router(client_visits_router, prefix="/client_visits", tags=["ClientVisits"])
    app.include_router(employee_vehicle_router, prefix="/employee_vehicles", tags=["EmployeeVehicles"])
    app.include_router(purchases.router)
    app.include_router(employee_map_router)
    app.include_router(brands_router, prefix="/brands", tags=["Brands"])
    app.include_router(lent.router, prefix="/lent", tags=["Lent"])
    app.include_router(sales_router, prefix="/sales", tags=["Sales"])
    app.include_router(payments.router, prefix="/payments", tags=["Payments"])
    
    return app

app = create_app()
