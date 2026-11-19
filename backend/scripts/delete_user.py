import sys

from app.db.database import SessionLocal
from app.db.models import ChatLog, Message, Ticket, User

if len(sys.argv) != 2:
    print("Usage: python -m scripts.delete_user <username>")
    sys.exit(1)

username = sys.argv[1]
db = SessionLocal()
try:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User '{username}' not found.")
    else:
        for model in (ChatLog, Message, Ticket):
            db.query(model).filter(model.user_id == user.id).delete()
        db.delete(user)
        db.commit()
        print(f"User '{username}' and their messages, tickets and logs were deleted.")
finally:
    db.close()