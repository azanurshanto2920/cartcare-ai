from app.db.database import SessionLocal
from app.db.models import Message

db = SessionLocal()
try:
    bad = []
    for m in db.query(Message).filter(Message.role == "assistant").order_by(Message.id).all():
        text = m.content or ""
        if "Sorry, I made" in text or "…" in text or "..." in text:
            bad.append(m)

    if not bad:
        print("No broken replies found.")
    else:
        to_delete = []
        print("These messages look broken and will be deleted with the question before each one:")
        for m in bad:
            question = (
                db.query(Message)
                .filter(Message.user_id == m.user_id, Message.role == "user", Message.id < m.id)
                .order_by(Message.id.desc())
                .first()
            )
            if question:
                to_delete.append(question)
                print(f"  question {question.id}: {question.content[:70]!r}")
            to_delete.append(m)
            print(f"  reply    {m.id}: {m.content[:70]!r}")

        if input("\nDelete these messages? Type yes to confirm: ").strip().lower() == "yes":
            for item in {x.id: x for x in to_delete}.values():
                db.delete(item)
            db.commit()
            print("Deleted.")
        else:
            print("Nothing was deleted.")
finally:
    db.close()