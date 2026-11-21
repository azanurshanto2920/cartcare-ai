from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = "postgresql://" + database_url[len("postgres://"):]
if database_url.startswith("postgresql://"):
    # Use the psycopg2 driver explicitly (psycopg2-binary is in requirements.txt)
    database_url = "postgresql+psycopg2://" + database_url[len("postgresql://"):]

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()