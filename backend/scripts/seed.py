from datetime import datetime, timedelta, timezone

from app.db.database import SessionLocal
from app.db.models import Customer, Order, OrderItem, Product

PRODUCTS = [
    # name, category, brand, price (USD), stock, description
    ("Samsung 43 inch Full HD Smart TV", "TV", "Samsung", 429, 12, "43 inch Full HD LED smart TV with built-in Wi-Fi and streaming apps. 1 year warranty."),
    ("Sony Bravia 55 inch 4K Google TV", "TV", "Sony", 999, 6, "55 inch 4K UHD Google TV with HDR and Dolby Audio. 2 years warranty."),
    ("TCL 32 inch HD LED TV", "TV", "TCL", 169, 20, "32 inch HD LED TV with HDMI and USB ports. 1 year warranty."),
    ("LG 65 inch 4K OLED TV", "TV", "LG", 2199, 3, "65 inch 4K OLED TV with perfect blacks and webOS. 2 years warranty."),
    ("Whirlpool 250L Double Door Refrigerator", "Refrigerator", "Whirlpool", 479, 10, "250 litre frost-free double door refrigerator with inverter compressor. 5 years compressor warranty."),
    ("Samsung 320L Double Door Refrigerator", "Refrigerator", "Samsung", 749, 5, "320 litre frost-free refrigerator with digital inverter and 10 years compressor warranty."),
    ("LG 190L Single Door Refrigerator", "Refrigerator", "LG", 329, 14, "190 litre direct-cool single door refrigerator, energy efficient. 1 year warranty."),
    ("Hisense 500L Side by Side Refrigerator", "Refrigerator", "Hisense", 1399, 2, "500 litre side by side refrigerator with water dispenser. 2 years warranty."),
    ("Gree 1 Ton Split AC", "AC", "Gree", 449, 9, "1 ton split air conditioner, non-inverter. 1 year warranty, 5 years compressor warranty."),
    ("Carrier 1.5 Ton Inverter AC", "AC", "Carrier", 749, 7, "1.5 ton inverter split AC, saves up to 50 percent electricity. 3 years warranty."),
    ("Midea 2 Ton Inverter AC", "AC", "Midea", 949, 4, "2 ton inverter split AC with fast cooling and auto clean. 3 years warranty."),
    ("General 1.5 Ton Split AC", "AC", "General", 829, 0, "1.5 ton split AC with turbo cooling. Currently out of stock."),
]

CUSTOMERS = [
    ("Daniel Carter", "daniel.carter@example.com", "+1-555-0101"),
    ("Emily Brooks", "emily.brooks@example.com", "+1-555-0102"),
    ("Michael Reyes", "michael.reyes@example.com", "+1-555-0103"),
    ("Sophie Turner", "sophie.turner@example.com", "+1-555-0104"),
    ("Omar Haddad", "omar.haddad@example.com", "+1-555-0105"),
]

# customer index, status, tracking number, days ago, [(product index, quantity)]
ORDERS = [
    (0, "delivered", "TRK1001", 20, [(0, 1)]),
    (0, "shipped", "TRK1002", 3, [(8, 1)]),
    (1, "processing", None, 1, [(4, 1), (2, 1)]),
    (2, "delivered", "TRK1003", 15, [(9, 1)]),
    (3, "cancelled", None, 9, [(1, 1)]),
    (4, "shipped", "TRK1004", 2, [(6, 1)]),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            print("Database already has products. Skipping seed.")
            return

        products = []
        for name, category, brand, price, stock, description in PRODUCTS:
            product = Product(
                name=name,
                category=category,
                brand=brand,
                price=price,
                stock=stock,
                description=description,
            )
            db.add(product)
            products.append(product)

        customers = []
        for name, email, phone in CUSTOMERS:
            customer = Customer(name=name, email=email, phone=phone)
            db.add(customer)
            customers.append(customer)

        db.flush()  # assigns ids to products and customers

        for customer_index, status, tracking, days_ago, items in ORDERS:
            total = sum(products[p].price * qty for p, qty in items)
            order = Order(
                customer_id=customers[customer_index].id,
                status=status,
                total=total,
                tracking_number=tracking,
                created_at=utc_now() - timedelta(days=days_ago),
            )
            db.add(order)
            db.flush()

            for product_index, qty in items:
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=products[product_index].id,
                        quantity=qty,
                        unit_price=products[product_index].price,
                    )
                )

        db.commit()
        print(
            f"Seeded {len(PRODUCTS)} products, {len(CUSTOMERS)} customers, {len(ORDERS)} orders."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()