from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat
from app.db import models  # noqa: F401  (registers the tables)
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CartCare AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}