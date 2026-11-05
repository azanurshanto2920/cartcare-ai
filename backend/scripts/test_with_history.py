import time

from app.db.database import SessionLocal
from app.db.models import Message
from app.services.agent import generate_reply_with_tools
from app.services.llm import build_user_turn
from app.services.rag import search_context

USER_ID = 1
HISTORY_LIMIT = 10
QUESTION = "Which air conditioners do you have under $800?"
RUNS = 3

db = SessionLocal()
try:
    recent = (
        db.query(Message)
        .filter(Message.user_id == USER_ID)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    recent.reverse()
    history = [{"role": m.role, "content": m.content} for m in recent]

    print("Saved history that is sent to the model:")
    for m in recent:
        print(f"  [{m.role}] {m.content[:90]!r}")

    for run in range(1, RUNS + 1):
        tools: list[str] = []
        started = time.perf_counter()
        turn = build_user_turn(QUESTION, search_context(QUESTION))
        reply = generate_reply_with_tools(db, USER_ID, history, turn, tools)
        seconds = time.perf_counter() - started
        print(f"\nRun {run} ({seconds:.1f}s, tools: {','.join(tools) or '-'})")
        print(reply[:500])
finally:
    db.close()