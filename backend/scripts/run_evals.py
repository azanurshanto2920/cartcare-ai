import sys

from sqlalchemy import func

from app.db.database import SessionLocal
from app.db.models import Ticket
from app.services.agent import generate_reply_with_tools, looks_broken
from app.services.llm import build_user_turn
from app.services.rag import search_context

USER_ID = 1
RUNS = 2  # each case is run this many times, because model replies can vary

CASES = [
    {
        "name": "ACs under 800 dollars",
        "question": "Which air conditioners do you have under $800?",
        "tools": ["search_products"],
        "contains": ["Gree", "Carrier"],
        "not_contains": ["Midea", "General"],
    },
    {
        "name": "Refrigerators under 500 dollars",
        "question": "Which refrigerators do you have under $500?",
        "tools": ["search_products"],
        "contains": ["LG", "Whirlpool"],
        "not_contains": ["Samsung", "Hisense"],
    },
    {
        "name": "TVs under 200 dollars",
        "question": "Do you have any TVs under $200?",
        "tools": ["search_products"],
        "contains": ["TCL"],
        "not_contains": ["Sony", "Samsung", "LG"],
    },
    {
        "name": "Out of stock product",
        "question": "Is the General 1.5 Ton Split AC in stock?",
        "any_of": ["out of stock", "not in stock", "unavailable", "currently out"],
    },
    {
        "name": "Return policy",
        "question": "What is your return policy?",
        "contains": ["7 days"],
    },
    {
        "name": "Free delivery",
        "question": "Do you offer free delivery?",
        "contains": ["200"],
    },
    {
        "name": "AC warranty",
        "question": "How long is the warranty on your air conditioners?",
        "any_of": ["1 to 3", "compressor"],
    },
    {
        "name": "Order lookup with the right email",
        "question": "Where is my order number 2? My email is daniel.carter@example.com",
        "tools": ["get_order_status"],
        "contains": ["TRK1002"],
    },
    {
        "name": "Order lookup with the wrong email",
        "question": "Where is my order number 2? My email is emily.brooks@example.com",
        "tools": ["get_order_status"],
        "not_contains": ["TRK1002"],
    },
    {
        "name": "Order lookup without an email",
        "question": "Where is my order number 2?",
        "forbidden_tools": ["get_order_status"],
        "any_of": ["email"],
        "not_contains": ["TRK1002"],
    },
    {
        "name": "Asks for a human",
        "question": "I want to speak to a human agent.",
        "tools": ["request_human_handoff"],
    },
    {
        "name": "Damaged product",
        "question": "My refrigerator arrived damaged and I want someone to help me.",
        "tools": ["request_human_handoff"],
    },
    {
        "name": "Greeting",
        "question": "Hi",
        "forbidden_tools": ["request_human_handoff"],
        "not_contains": ["$"],
    },
    {
        "name": "Question outside the store",
        "question": "What is the capital of France?",
        "forbidden_tools": ["get_order_status", "search_products"],
        "not_contains": ["Paris"],
    },
]


def normalize(text: str) -> str:
    # Models sometimes use special space characters (for example a narrow no-break space)
    return " ".join(text.split()).lower()


def check(case: dict, reply: str, tools: list[str]) -> list[str]:
    problems = []
    lowered = normalize(reply)

    if looks_broken(reply):
        problems.append("the reply looks broken")
    for text in case.get("contains", []):
        if normalize(text) not in lowered:
            problems.append(f"missing {text!r}")
    options = case.get("any_of")
    if options and not any(normalize(option) in lowered for option in options):
        problems.append(f"none of {options} found")
    for text in case.get("not_contains", []):
        if normalize(text) in lowered:
            problems.append(f"should not contain {text!r}")
    for tool in case.get("tools", []):
        if tool not in tools:
            problems.append(f"tool {tool} was not used")
    for tool in case.get("forbidden_tools", []):
        if tool in tools:
            problems.append(f"tool {tool} should not have been used")
    return problems


def main() -> None:
    db = SessionLocal()
    last_ticket_id = db.query(func.max(Ticket.id)).scalar() or 0
    passed = 0
    total = 0
    failed_cases = []

    try:
        for case in CASES:
            case_failed = False
            print(f"\n{case['name']}")
            for run in range(1, RUNS + 1):
                total += 1
                tools: list[str] = []
                try:
                    turn = build_user_turn(case["question"], search_context(case["question"]))
                    reply = generate_reply_with_tools(db, USER_ID, [], turn, tools)
                except Exception as e:
                    db.rollback()
                    print(f"  run {run}: ERROR {str(e)[:150]}")
                    case_failed = True
                    continue

                problems = check(case, reply, tools)
                if problems:
                    case_failed = True
                    print(f"  run {run}: FAIL (tools: {','.join(tools) or '-'})")
                    for problem in problems:
                        print(f"    - {problem}")
                    print(f"    reply: {reply[:200]!r}")
                else:
                    passed += 1
                    print(f"  run {run}: pass (tools: {','.join(tools) or '-'})")
            if case_failed:
                failed_cases.append(case["name"])
    finally:
        # Remove the tickets that these test runs created
        removed = db.query(Ticket).filter(Ticket.id > last_ticket_id).delete()
        db.commit()
        db.close()
        if removed:
            print(f"\nRemoved {removed} test ticket(s).")

    print(f"\nPassed {passed} of {total} runs.")
    if failed_cases:
        print("Cases with a problem: " + ", ".join(failed_cases))
        sys.exit(1)


if __name__ == "__main__":
    main()