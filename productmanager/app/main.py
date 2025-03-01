# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import engine
from app.db.base import Base
from app.routers.employees import router as employees_router
from app.routers.auth import auth_router
from app.routers import employees, clients, products, orders, lent, purchases
from app.routers.employee_clients import router as employee_clients_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.client_visits import router as client_visits_router
from app.routers.employee_vehicle import router as employee_vehicle_router
from app.routers.sales import router as sales_router
from app.routers.brands import router as brands_router
from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models.employees import Employee
from app.models.sales import Sales

from app.db.base import Base



@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    # print("Registered tables before DB creation:", Base.metadata.tables.keys())

    Base.metadata.drop_all(bind=engine)  # ✅ 기존 테이블 삭제
    Base.metadata.create_all(bind=engine, )  # ✅ 테이블 재생성

    # print("Registered tables after DB creation:", Base.metadata.tables.keys()) 
    db = SessionLocal()
    try:
        admin = db.query(Employee).filter(Employee.id == 1).first()
        if not admin:
            hashed_pw = get_password_hash("admin123")  # 초기 비밀번호 설정
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
    app.include_router(purchases.router)
    app.include_router(sales_router, prefix="/sales", tags=["Sales"])
    app.include_router(brands_router, prefix="/brands", tags=["Brands"])
    app.include_router(lent.router, prefix="/lent", tags=["Lent"])
    app.include_router(sales_router, prefix="/sales", tags=["Sales"])
    return app

app = create_app()


