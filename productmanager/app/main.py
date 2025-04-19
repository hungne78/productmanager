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
from app.routers.category_price_override import router as category_price_override_router
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
from app.utils.monthly_aggregation import aggregate_sales_to_monthly
from app.routers.monthly_sales import router as monthly_sales_router
from app.models.admin_users import AdminUser  # ✅ 이 줄이 꼭 필요함
from app.models.brands import Brand
from app.models.category_price_override import CategoryPriceOverride
from app.models.client_prices import ClientProductPrice
from app.models.client_visit_archive import ClientVisitArchive
from app.models.clients import Client
from app.models.company import CompanyInfo
from app.models.employee_clients import EmployeeClient
from app.models.employee_vehicle import EmployeeVehicle
from app.models.franchise_order_archive import FranchiseOrderArchive
from app.models.franchise_order import FranchiseOrder
from app.models.lent import Lent
from app.models.monthly_sales import MonthlySales

from app.models.orders import Order, OrderItem
from app.models.payments import Payment
from app.models.product_barcodes import ProductBarcode
from app.models.product_purchase_prices import ProductPurchasePrice
from app.models.purchases import Purchase
from app.models.purchase_archive import PurchaseArchive
from app.models.sales_record_archive import SalesRecordArchive
from app.models.sales import Sales
from app.routers.admin_auth  import router as admin_auth_router 
from app.utils.archive_utils import migrate_last_year_sales
from app.utils.archive_utils import archive_orders_for_year_if_not_archived
# 기존 scheduler 초기화 이후에 추가
from sqlalchemy import text
from datetime import datetime

def run_monthly_aggregation():
    from app.db.database import SessionLocal
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    today = datetime.now()
    # 집계 대상: 전달 기준 (ex. 2025-04-01 → 2025-03)
    year = today.year
    month = today.month - 1
    if month == 0:
        year -= 1
        month = 12

    db = SessionLocal()
    try:
        aggregate_sales_to_monthly(db, year, month)
    except Exception as e:
        print(f"❌ [월간 집계 오류] {e}")
    finally:
        db.close()
        
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
def migrate_task():
    db = SessionLocal()
    try:
        migrate_last_year_sales(db)
    finally:
        db.close()

def run_yearly_order_archive():
    from datetime import datetime
    yr = datetime.now().year - 1
    with SessionLocal() as db:
        archive_orders_for_year_if_not_archived(yr, db)

def archive_purchase_data():
    """
    전년도 매입 데이터를 purchases_YYYY 테이블로 이관 후 본 테이블 정리
    """
    prev_year = datetime.now().year - 1
    table_name = f"purchases_{prev_year}"
    with engine.begin() as conn:
        print(f"📦 [Scheduler] {prev_year}년 매입 테이블 생성 및 이관 시작")

        # 1️⃣ 테이블 복제 (없으면 생성)
        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE purchases"))

        # 2️⃣ 데이터 이관
        conn.execute(text(f"""
            INSERT INTO {table_name}
            SELECT * FROM purchases
            WHERE YEAR(purchase_date) = :year
        """), {"year": prev_year})

        # 3️⃣ 원본 테이블 삭제
        conn.execute(text("DELETE FROM purchases WHERE YEAR(purchase_date) = :year"), {"year": prev_year})

        print(f"✅ [Scheduler] {prev_year}년 매입 이관 완료")
def archive_client_visits():
    prev_year = datetime.now().year - 1
    table_name = f"client_visits_{prev_year}"

    with engine.begin() as conn:
        print(f"📌 [Scheduler] {prev_year}년 client_visits 테이블 생성 및 이관 시작")

        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE client_visits"))
        conn.execute(text(f"""
            INSERT INTO {table_name}
            SELECT * FROM client_visits WHERE YEAR(visit_date) = :year
        """), {"year": prev_year})
        conn.execute(text("DELETE FROM client_visits WHERE YEAR(visit_date) = :year"), {"year": prev_year})

        print(f"✅ [Scheduler] {prev_year}년 client_visits 이관 완료")
def archive_franchise_orders():
    prev_year = datetime.now().year - 1

    order_table = f"franchise_orders_{prev_year}"
    item_table  = f"franchise_order_items_{prev_year}"

    with engine.begin() as conn:
        print(f"📦 [Scheduler] {prev_year}년 프랜차이즈 주문 이관 시작")

        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {order_table} LIKE franchise_orders"))
        conn.execute(text(f"CREATE TABLE IF NOT EXISTS {item_table} LIKE franchise_order_items"))

        conn.execute(text(f"""
            INSERT INTO {order_table}
            SELECT * FROM franchise_orders
            WHERE YEAR(order_date) = :year
        """), {"year": prev_year})

        conn.execute(text(f"""
            INSERT INTO {item_table}
            SELECT i.*
            FROM franchise_order_items i
            JOIN franchise_orders o ON i.order_id = o.id
            WHERE YEAR(o.order_date) = :year
        """), {"year": prev_year})

        conn.execute(text("""
            DELETE FROM franchise_order_items
            WHERE order_id IN (
                SELECT id FROM franchise_orders WHERE YEAR(order_date) = :year
            )
        """), {"year": prev_year})

        conn.execute(text("DELETE FROM franchise_orders WHERE YEAR(order_date) = :year"), {"year": prev_year})

        print(f"✅ [Scheduler] {prev_year}년 프랜차이즈 주문 이관 완료")

scheduler = BackgroundScheduler()
scheduler.add_job(run_monthly_aggregation, "cron", day=1, hour=3, minute=10)  # 매월 1일 03:10
scheduler.add_job(migrate_task,
                  trigger="cron",
                  month=1, day=1, hour=2, minute=0,
                  id="migrate_sales_last_year")

scheduler.add_job(
    run_yearly_order_archive,
    trigger="cron",           # 매년 1‑1 03:00
    month=1, day=1, hour=3, minute=0
)



scheduler.add_job(archive_purchase_data, 'cron', month=1, day=1, hour=0, minute=0, id="archive_purchase_data")
scheduler.add_job(archive_client_visits, 'cron', month=1, day=1, hour=1, minute=0, id="archive_client_visits")
scheduler.add_job(archive_franchise_orders, 'cron', month=1, day=1, hour=4, minute=0, id="archive_franchise_orders")
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
    print("📦 현재 연결된 DB 주소:", engine.url)
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
        default_admins = [
            {
                "email": "hcjang0528@naver.com",
                "name": "장현철",
                "password": "admin123"
            },
            {
                "email": "kimdoohan@naver.com",
                "name": "김두한",
                "password": "admin123"
            }
        ]
        from app.utils.archive_utils import archive_sales_for_year_if_not_archived
        from datetime import datetime
        last_year = datetime.now().year - 1
        archive_sales_for_year_if_not_archived(last_year, db)

        for admin_data in default_admins:
            existing_admin = db.query(AdminUser).filter(AdminUser.email == admin_data["email"]).first()
            if not existing_admin:
                new_admin = AdminUser(
                    email=admin_data["email"],
                    name=admin_data["name"],
                    role="admin",
                    password_hash=get_password_hash(admin_data["password"])
                )
                db.add(new_admin)
                print(f"✅ 기본 관리자 계정 생성됨: {admin_data['email']}")
        db.commit()        
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
    app.include_router(category_price_override_router, prefix="/category_price_overrides", tags=["CategoryPriceOverride"])
    app.include_router(monthly_sales_router, prefix="/monthly_sales", tags=["MonthlySales"])
    app.include_router(admin_auth_router, prefix="/admin_auth", tags=["AdminUser"])
    return app

app = create_app()
