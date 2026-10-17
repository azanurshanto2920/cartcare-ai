from sqlalchemy import inspect, text

from app.db.database import engine

columns = [c["name"] for c in inspect(engine).get_columns("users")]

if "is_admin" in columns:
    print("Column is_admin already exists. Nothing to do.")
else:
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
    print("Column is_admin added.")