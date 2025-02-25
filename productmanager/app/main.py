# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import engine
from app.db.base import Base
from app.routers.employees import router as employees_router
from app.routers.auth import auth_router
from app.routers import employees, clients, products, orders
from app.routers.employee_clients import router as employee_clients_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.client_visits import router as client_visits_router
from app.routers.employee_vehicle import router as employee_vehicle_router
from app.routers.sales import router as sales_router
from app.routers.brands import router as brands_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    Base.metadata.create_all(bind=engine)
    print("Startup: Created all tables")

    yield  # <-- 여기서 FastAPI가 실행됨

    # --- SHUTDOWN LOGIC ---
    print("Shutdown: Cleaning up...")

def create_app() -> FastAPI:
    # FastAPI에 lifespan 함수를 등록
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        redirect_slashes=False, 
    )
    # CORS 미들웨어 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],       # 모든 도메인 허용 (배포 시 주의)
        allow_credentials=True,
        allow_methods=["*"],       # 모든 메서드 허용 (GET, POST, OPTIONS, ...)
        allow_headers=["*"],       # 모든 헤더 허용
    )
    # 로그인 라우터(prefix="" → "/login")
    app.include_router(auth_router, prefix="", tags=["Auth"])
    # Include routers
    app.include_router(employees.router, prefix="/employees", tags=["Employees"])
    app.include_router(clients.router, prefix="/clients", tags=["Clients"])
    app.include_router(products.router, prefix="/products", tags=["Products"])
    app.include_router(orders.router, prefix="/orders", tags=["Orders"])
    app.include_router(employee_clients_router, prefix="/employee_clients", tags=["Employee-Client"])
    app.include_router(client_visits_router, prefix="/client_visits", tags=["ClientVisits"])
    app.include_router(employee_vehicle_router, prefix="/employee_vehicles", tags=["EmployeeVehicles"])
    app.include_router(employee_vehicle_router, prefix="/employee_vehicles", tags=["EmployeeVehicles"])
    app.include_router(sales_router, prefix="/sales", tags=["Sales"])
    app.include_router(brands_router, prefix="/brands", tags=["Brands"])
    return app

app = create_app()

@app.get("/")
def root():
    return {"message": "Hello from FastAPI project!"}
