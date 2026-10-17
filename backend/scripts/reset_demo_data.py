from app.db.database import SessionLocal
from app.db.models import Customer, Message, Order, OrderItem, Product, Ticket
from scripts.seed import seed


def reset() -> None:
    db = SessionLocal()
    try:
        # Delete children before parents because of foreign keys
        for model in (OrderItem, Order, Customer, Product, Ticket, Message):
            db.query(model).delete()
        db.commit()
        print("Cleared shop data, tickets and chat history. User accounts are kept.")
    finally:
        db.close()

    seed()


if __name__ == "__main__":
    reset()