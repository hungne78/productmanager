# app/models/__init__.py

# ✅ Sales 모델을 먼저 로드하여 관계 문제 해결
from app.models.sales import Sales

from app.models.employees import Employee
from app.models.clients import Client
from app.models.brands import Brand
from app.models.products import Product
from app.models.purchases import Purchase
from app.models.client_prices import ClientProductPrice
from app.models.orders import Order, OrderItem
from app.models.payments import Payment
from app.models.sales_records import SalesRecord
from app.models.employee_clients import EmployeeClient
