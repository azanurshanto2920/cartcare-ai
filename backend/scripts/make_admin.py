import sys

from app.db.database import SessionLocal
from app.db.models import User

if len(sys.argv) != 2:
    print("Usage: python -m scripts.make_admin <username>")
    sys.exit(1)

username = sys.argv[1]
db = SessionLocal()
try:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User '{username}' not found.")
    else:
        user.is_admin = True
        db.commit()
        print(f"User '{username}' is now an admin.")
finally:
    db.close()