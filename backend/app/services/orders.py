from sqlalchemy.orm import Session

from app.db.models import Customer, Order, OrderItem, Product


def get_order_status(db: Session, order_id: int, email: str) -> dict:
    row = (
        db.query(Order, Customer)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(Order.id == order_id, Customer.email.ilike(email.strip()))
        .first()
    )

    # Same message for "no such order" and "wrong email", so nobody can probe order numbers
    if not row:
        return {"found": False, "message": "No order found with that order number and email."}

    order, customer = row

    items = (
        db.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    return {
        "found": True,
        "order_id": order.id,
        "customer_name": customer.name,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "total": order.total,
        "placed_on": order.created_at.strftime("%Y-%m-%d"),
        "items": [
            {
                "product": product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item, product in items
        ],
    }