from collections import Counter
from datetime import datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import ChatLog, InvoiceRecord, Ticket

DAYS = 7


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_analytics(db: Session) -> dict:
    logs = db.query(ChatLog).all()

    total = len(logs)
    failed = sum(1 for log in logs if log.failed)

    # Tool usage and human handoffs
    tool_counts: Counter = Counter()
    handoffs = 0
    for log in logs:
        names = [name for name in (log.tools or "").split(",") if name]
        tool_counts.update(names)
        if "request_human_handoff" in names:
            handoffs += 1

    # Response times
    durations = sorted(log.duration_ms for log in logs if log.duration_ms)
    average_ms = round(sum(durations) / len(durations)) if durations else 0
    median_ms = durations[len(durations) // 2] if durations else 0
    slowest_ms = durations[-1] if durations else 0

    # Chats per day for the last DAYS days (UTC dates)
    today = utc_now().date()
    first_day = today - timedelta(days=DAYS - 1)
    per_day = Counter(
        log.created_at.date() for log in logs if log.created_at and log.created_at.date() >= first_day
    )
    daily = [
        {"date": (first_day + timedelta(days=i)).isoformat(), "chats": per_day.get(first_day + timedelta(days=i), 0)}
        for i in range(DAYS)
    ]
    last_week = sum(item["chats"] for item in daily)

    # Questions that failed or ended in a handoff are the most useful ones to review
    needs_attention = [
        {
            "id": log.id,
            "question": (log.question or "")[:140],
            "reason": "Failed" if log.failed else "Handed to a human agent",
            "created_at": log.created_at,
        }
        for log in sorted(logs, key=lambda item: item.id, reverse=True)
        if log.failed or "request_human_handoff" in (log.tools or "")
    ][:8]

    open_tickets = db.query(Ticket).filter(Ticket.status == "open").count()
    resolved_tickets = db.query(Ticket).filter(Ticket.status == "resolved").count()
    invoices_total = db.query(InvoiceRecord).count()
    invoices_flagged = db.query(InvoiceRecord).filter(InvoiceRecord.needs_review.is_(True)).count()

    return {
        "chats_total": total,
        "chats_last_week": last_week,
        "failed": failed,
        "failure_rate": round(failed / total * 100, 1) if total else 0,
        "handoffs": handoffs,
        "handoff_rate": round(handoffs / total * 100, 1) if total else 0,
        "average_ms": average_ms,
        "median_ms": median_ms,
        "slowest_ms": slowest_ms,
        "tools": [{"name": name, "count": count} for name, count in tool_counts.most_common()],
        "daily": daily,
        "needs_attention": needs_attention,
        "tickets": {"open": open_tickets, "resolved": resolved_tickets},
        "invoices": {"total": invoices_total, "needs_review": invoices_flagged},
    }