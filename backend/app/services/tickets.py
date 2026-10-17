from sqlalchemy.orm import Session

from app.db.models import Message, Ticket

CONVERSATION_LIMIT = 10


def create_ticket(db: Session, user_id: int, reason: str) -> dict:
    recent = (
        db.query(Message)
        .filter(Message.user_id == user_id)
        .order_by(Message.id.desc())
        .limit(CONVERSATION_LIMIT)
        .all()
    )
    recent.reverse()
    conversation = "\n".join(f"{m.role}: {m.content}" for m in recent)

    # Do not create a second open ticket for the same user
    existing = (
        db.query(Ticket)
        .filter(Ticket.user_id == user_id, Ticket.status == "open")
        .first()
    )
    if existing:
        return {
            "ticket_id": existing.id,
            "status": "already_open",
            "message": "A human support agent has already been requested for this customer.",
        }

    ticket = Ticket(user_id=user_id, reason=reason, conversation=conversation)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "ticket_id": ticket.id,
        "status": "created",
        "message": "A human support agent will contact the customer.",
    }