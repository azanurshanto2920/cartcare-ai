from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, chat
from app.bootstrap import start_bootstrap_in_background
from app.core.config import settings
from app.db import models  # noqa: F401  (registers the tables)
from app.db.database import Base, engine

if settings.environment == "production" and settings.jwt_secret in ("", "change-me"):
    raise RuntimeError("JWT_SECRET must be set to a long random value in production")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CartCare AI")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup() -> None:
    start_bootstrap_in_background()


@app.get("/health")
def health():
    return {"status": "ok"}