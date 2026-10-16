from datetime import datetime, timedelta

from app.db.database import SessionLocal
from app.db.models import Customer, Order, OrderItem, Product

PRODUCTS = [
    # name, category, brand, price (BDT), stock, description
    ("Samsung 43 inch Full HD Smart TV", "TV", "Samsung", 48500, 12, "43 inch Full HD LED smart TV with built-in Wi-Fi and streaming apps. 1 year warranty."),
    ("Sony Bravia 55 inch 4K Google TV", "TV", "Sony", 112000, 6, "55 inch 4K UHD Google TV with HDR and Dolby Audio. 2 years warranty."),
    ("Walton 32 inch HD LED TV", "TV", "Walton", 19500, 20, "32 inch HD LED TV with HDMI and USB ports. 1 year warranty."),
    ("LG 65 inch 4K OLED TV", "TV", "LG", 245000, 3, "65 inch 4K OLED TV with perfect blacks and webOS. 2 years warranty."),
    ("Walton 250L Double Door Refrigerator", "Refrigerator", "Walton", 36500, 10, "250 litre frost-free double door refrigerator with inverter compressor. 5 years compressor warranty."),
    ("Samsung 320L Double Door Refrigerator", "Refrigerator", "Samsung", 62000, 5, "320 litre frost-free refrigerator with digital inverter and 10 years compressor warranty."),
    ("LG 190L Single Door Refrigerator", "Refrigerator", "LG", 27500, 14, "190 litre direct-cool single door refrigerator, energy efficient. 1 year warranty."),
    ("Hisense 500L Side by Side Refrigerator", "Refrigerator", "Hisense", 118000, 2, "500 litre side by side refrigerator with water dispenser. 2 years warranty."),
    ("Gree 1 Ton Split AC", "AC", "Gree", 41500, 9, "1 ton split air conditioner, non-inverter. 1 year warranty, 5 years compressor warranty."),
    ("Carrier 1.5 Ton Inverter AC", "AC", "Carrier", 69500, 7, "1.5 ton inverter split AC, saves up to 50 percent electricity. 3 years warranty."),
    ("Midea 2 Ton Inverter AC", "AC", "Midea", 88000, 4, "2 ton inverter split AC with fast cooling and auto clean. 3 years warranty."),
    ("General 1.5 Ton Split AC", "AC", "General", 79500, 0, "1.5 ton split AC with turbo cooling. Currently out of stock."),
]

CUSTOMERS = [
    ("Rahim Uddin", "rahim@example.com", "01711000001"),
    ("Karima Begum", "karima@example.com", "01711000002"),
    ("Tanvir Ahmed", "tanvir@example.com", "01711000003"),
    ("Nusrat Jahan", "nusrat@example.com", "01711000004"),
    ("Sajib Hossain", "sajib@example.com", "01711000005"),
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
                created_at=datetime.utcnow() - timedelta(days=days_ago),
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