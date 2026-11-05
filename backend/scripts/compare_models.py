import time

from app.core.config import settings
from app.db.database import SessionLocal
from app.services.agent import generate_reply_with_tools
from app.services.llm import build_user_turn
from app.services.rag import search_context

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
QUESTIONS = [
    "Which air conditioners do you have under $800?",
    "Where is my order number 2? My email is daniel.carter@example.com",
    "What is your return policy?",
]
RUNS = 2
USER_ID = 1


def looks_broken(reply: str) -> bool:
    lowered = reply.lower()
    return (
        "..." in reply
        or "<think" in lowered
        or "sorry" in lowered
        or "apolog" in lowered
        or len(reply) > 700
    )


def main() -> None:
    db = SessionLocal()
    original_model = settings.llm_model
    try:
        for model in MODELS:
            settings.llm_model = model
            print(f"\n=== {model} ===")
            broken = 0
            total = 0

            for question in QUESTIONS:
                for run in range(1, RUNS + 1):
                    total += 1
                    tools: list[str] = []
                    started = time.perf_counter()
                    try:
                        turn = build_user_turn(question, search_context(question))
                        reply = generate_reply_with_tools(db, USER_ID, [], turn, tools)
                    except Exception as e:
                        broken += 1
                        print(f"[error] {question[:40]} (run {run}): {str(e)[:200]}")
                        db.rollback()
                        continue

                    seconds = time.perf_counter() - started
                    flagged = looks_broken(reply)
                    broken += int(flagged)
                    label = "CHECK" if flagged else "ok"
                    print(f"[{label}] {question[:40]} (run {run}) | tools: {','.join(tools) or '-'} | {seconds:.1f}s")
                    print("    " + reply[:400].replace("\n", "\n    "))

            print(f"--- {model}: {broken} of {total} flagged ---")
    finally:
        settings.llm_model = original_model
        db.close()


if __name__ == "__main__":
    main()