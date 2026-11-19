import threading
from pathlib import Path

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal
from app.db.models import User
from app.services.rag import chunk_text, index_document, list_documents

POLICY_FILE = Path(__file__).resolve().parents[1] / "data" / "store_policies.txt"


def ensure_admin() -> None:
    if not settings.admin_username or not settings.admin_password:
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.admin_username).first()
        if user is None:
            db.add(
                User(
                    username=settings.admin_username,
                    hashed_password=hash_password(settings.admin_password),
                    is_admin=True,
                )
            )
            db.commit()
            print(f"Bootstrap: created admin '{settings.admin_username}'")
    finally:
        db.close()


def ensure_demo_store() -> None:
    # Imported here so the app still starts if the scripts folder is missing
    from scripts.seed import seed

    seed()  # does nothing when products already exist


def ensure_policies() -> None:
    if list_documents():
        return
    if not POLICY_FILE.exists():
        print(f"Bootstrap: policy file not found at {POLICY_FILE}")
        return

    text = POLICY_FILE.read_text(encoding="utf-8")
    count = index_document(POLICY_FILE.name, chunk_text(text))
    print(f"Bootstrap: loaded {count} policy sections")


def run_bootstrap() -> None:
    # Every step is independent: one failure must not stop the others or the server
    for step in (ensure_admin, ensure_demo_store, ensure_policies):
        try:
            step()
        except Exception as e:
            print(f"Bootstrap step {step.__name__} failed: {e}")


def start_bootstrap_in_background() -> None:
    # The embedding model can take a while to load on the first start, so do not block the server
    threading.Thread(target=run_bootstrap, daemon=True).start()