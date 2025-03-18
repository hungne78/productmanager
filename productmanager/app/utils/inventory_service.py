from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from app.models.employee_inventory import EmployeeInventory
from app.models.sales_records import SalesRecord
from app.models.orders import Order, OrderItem

def update_vehicle_stock(employee_id: int, db: Session, order_date: date):
    """
    '실시간 판매 차감' 방식을 쓴다면,
    여기서는 '출고분'만 더해주면 됨.
    """
    # 1) 현재 재고
    inv_list = db.query(EmployeeInventory).filter(EmployeeInventory.employee_id == employee_id).all()
    stock_map = {item.product_id: item.quantity for item in inv_list}

    # 2) 마지막 출고 차수
    last_shipment_round = (
        db.query(func.max(Order.shipment_round))
          .filter(Order.employee_id == employee_id, Order.order_date == order_date)
          .scalar()
    ) or 0

    # 3) 이번 차수( last_shipment_round ) 주문 => 재고+
    shipped_orders = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity))
          .join(Order, OrderItem.order_id == Order.id)
          .filter(
              Order.employee_id == employee_id,
              Order.order_date == order_date,
              Order.shipment_round == last_shipment_round
          )
          .group_by(OrderItem.product_id)
          .all()
    )

    for product_id, total_qty in shipped_orders:
        old_qty = stock_map.get(product_id, 0)
        new_qty = old_qty + total_qty
        stock_map[product_id] = new_qty
        print(f"[출고 반영] {product_id}: {old_qty}→{new_qty}")

    # 4) DB 반영
    for product_id, qty in stock_map.items():
        inv_item = (
            db.query(EmployeeInventory)
              .filter(EmployeeInventory.employee_id == employee_id,
                      EmployeeInventory.product_id == product_id)
              .one_or_none()
        )
        if inv_item:
            inv_item.quantity = qty
        else:
            db.add(EmployeeInventory(
                employee_id=employee_id,
                product_id=product_id,
                quantity=qty
            ))
    db.commit()

def subtract_inventory_on_sale(employee_id: int, product_id: int, sold_qty: int, db: Session):
    """
    상품 product_id를 sold_qty만큼 차량재고에서 즉시 차감(실시간) 하는 함수
    """
    # 1) 현재 해당 직원+상품의 재고 조회
    inv_item = (
        db.query(EmployeeInventory)
          .filter(EmployeeInventory.employee_id == employee_id,
                  EmployeeInventory.product_id == product_id)
          .one_or_none()
    )

    # 2) 만약 재고 정보가 없다면 새로 생성(초기 0)
    if not inv_item:
        inv_item = EmployeeInventory(
            employee_id=employee_id,
            product_id=product_id,
            quantity=0
        )
        db.add(inv_item)
        db.flush()

    # 3) 실제 차감
    old_qty = inv_item.quantity
    new_qty = old_qty - sold_qty
    if new_qty < 0:
        # 음수가 되는 걸 막을 수도 있고, 그냥 허용할 수도 있음
        new_qty = 0

    inv_item.quantity = new_qty
    db.commit()

    print(f"🔻 [실시간 판매 차감] 직원={employee_id}, 상품={product_id}, 수량={sold_qty}, 재고 {old_qty}→{new_qty}")

