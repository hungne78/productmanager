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
from app.routers.franchise_order import router as franchise_order_router
from app.routers.brands import router as brands_router
from app.routers.company import router as company_router
from app.routers.client_auth import router as client_auth_router
from app.core.security import get_password_hash
from app.routers import payments
from app.models.employees import Employee
from app.models.employee_inventory import EmployeeInventory
from app.models.orders_archive import OrderArchive , OrderItemArchive
from app.routers.employee_map_routers import router as employee_map_router
from app.routers import client_visits 
from app.routers.employee_inventory import router as employee_inventory_router  # ✅ 수정
from app.utils.time_utils import convert_utc_to_kst  # ✅ KST 변환 함수 추가
import json
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from fastapi.routing import APIRoute
from app.db.database import get_db
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.products import Product
from app.models.sales_records import SalesRecord
from app.utils.time_utils import get_kst_now
from dateutil.relativedelta import relativedelta

def cleanup_unused_products_task():
    db = SessionLocal()  # 직접 세션 획득
    try:
        six_months_ago = get_kst_now() - relativedelta(months=6)
        recent_sold_subq = (
            db.query(SalesRecord.product_id)
            .filter(SalesRecord.sale_datetime >= six_months_ago)
            .distinct()
            .subquery()
        )
        unused_products = (
            db.query(Product)
            .filter(Product.stock == 0)
            .filter(~Product.id.in_(recent_sold_subq))
            .all()
        )
        count = len(unused_products)
        for p in unused_products:
            db.delete(p)
        db.commit()
        print(f"[⏰ 자동삭제] {count}개 상품 삭제 완료")
    except Exception as e:
        print(f"❌ 자동삭제 오류: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()


logging.basicConfig(level=logging.DEBUG)  # DEBUG 레벨로 설정하여 모든 로그 출력
logger = logging.getLogger(__name__)

# ✅ `422 Unprocessable Content` 오류 발생 시 강제로 로그 출력

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ 서버 시작 및 종료 시 실행되는 코드 """
    # print("\n📡 [FastAPI] 등록된 엔드포인트 목록:")
    # for route in app.router.routes:
    #     if isinstance(route, APIRoute):
    #         print(f"➡️ {route.path} ({route.methods})")
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = db.query(Employee).filter(Employee.id == 1).first()
        if not admin:
            hashed_pw = get_password_hash("admin123")
            admin = Employee(
                password_hash=hashed_pw,
                name="김두한",
                phone="01036649876",
                role="admin"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Default admin created")
    finally:
        db.close()

    scheduler.add_job(cleanup_unused_products_task, "cron", hour=3, minute=0)
    scheduler.start()
    print("✅ 스케줄러 시작됨 (매일 03:00 자동 삭제)")
       
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
                content = response.body.decode("utf-8", errors="replace")  

                # ✅ JSON 변환 오류 방지
                content = json.loads(content)

                # ✅ KST 변환 적용
                if isinstance(content, dict):  
                    content = convert_utc_to_kst_recursive(content)
                elif isinstance(content, list):  
                    content = [convert_utc_to_kst_recursive(item) for item in content]

                # ✅ UTF-8 헤더 강제 설정
                return JSONResponse(content=content, headers={"Content-Type": "application/json; charset=utf-8"})
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
    # ✅ `422 Unprocessable Content` 오류 발생 시 강제로 로그 출력
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        print("🚨 [FastAPI] 422 오류 발생: 요청 검증 실패")  # ✅ 강제 출력
        logger.error(f"🚨 [422 오류 발생] 요청 경로: {request.url}")

        try:
            request_body = await request.json()
            logger.error(f"📡 [요청 데이터] {request_body}")
            print(f"📡 [요청 데이터] {request_body}")  # ✅ 강제 출력
        except Exception:
            logger.error("📡 [요청 데이터] 본문 없음")
            print("📡 [요청 데이터] 본문 없음")  # ✅ 강제 출력

        logger.error(f"❌ [FastAPI 오류 상세] {exc.errors()}")
        print(f"❌ [FastAPI 오류 상세] {exc.errors()}")  # ✅ 강제 출력

        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
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
    # print("✅ FastAPI 서버 시작: 라우터 등록 중...")  # ✅ 서버 시작 시 로그 추가
    app.include_router(employee_inventory_router, prefix="/inventory", tags=["Inventory"])
    # print("✅ /inventory 라우터 등록 완료!")  # ✅ 정상 등록 확인 로그
    app.include_router(company_router, prefix="/company", tags=["Company"]) 
    app.include_router(franchise_order_router, prefix="/franchise_orders", tags=["FranchiseOrders"])
    app.include_router(client_auth_router, prefix="/client_auth", tags=["ClientAuth"])
    return app

app = create_app()
