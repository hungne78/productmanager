from sqlalchemy.orm import Session
from app.models import Order, OrderItem, Product

def test_order_query(db: Session):
    employee_id = 3
    order_date = "2025-03-10"

    order_items = (
        db.query(
            OrderItem.product_id,
            OrderItem.quantity,
            Product.product_name,
            Product.category,
            Product.brand
        )
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .filter(Order.employee_id == employee_id, Order.order_date == order_date)
        .all()
    )

    if not order_items:
        print("❌ [테스트] 해당 직원의 주문 항목이 없습니다.")
    else:
        print(f"✅ [테스트] {len(order_items)}개 주문 항목 조회됨: {order_items}")
