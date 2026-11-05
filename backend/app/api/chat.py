import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import ChatLog, Message, User
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.agent import generate_reply_with_tools
from app.services.llm import build_user_turn
from app.services.rag import search_context

router = APIRouter(tags=["chat"])

HISTORY_LIMIT = 10


def save_log(
    db: Session,
    user_id: int,
    question: str,
    answer: str,
    tools: list[str],
    started: float,
    failed: bool,
) -> None:
    # Logging must never break a chat, so errors are only printed
    try:
        db.add(
            ChatLog(
                user_id=user_id,
                question=question,
                answer=answer,
                tools=",".join(tools),
                duration_ms=int((time.perf_counter() - started) * 1000),
                failed=failed,
            )
        )
        db.commit()
    except Exception as e:
        print(f"Could not save chat log: {e}")
        db.rollback()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()
    tools_used: list[str] = []

    # Load only this user's recent messages
    recent = (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    recent.reverse()
    history = [{"role": m.role, "content": m.content} for m in recent]

    # Store the user's message now (not committed yet) so a handoff ticket can include it
    db.add(Message(user_id=current_user.id, role="user", content=request.message))
    db.flush()

    # Search the knowledge base; continue without context if it fails
    try:
        doc_context = search_context(request.message)
    except Exception as e:
        print(f"RAG search error: {e}")
        doc_context = ""

    user_turn = build_user_turn(request.message, doc_context)

    try:
        ai_reply = generate_reply_with_tools(
            db, current_user.id, history, user_turn, tools_used
        )
    except Exception as e:
        print(f"LLM error: {e}")
        db.rollback()
        fallback = "Sorry, there was a problem generating a response. Please try again."
        save_log(db, current_user.id, request.message, fallback, tools_used, started, True)
        return ChatResponse(reply=fallback)

    # Save the assistant's reply; the user's message is already added above
    db.add(Message(user_id=current_user.id, role="assistant", content=ai_reply))
    db.commit()

    save_log(db, current_user.id, request.message, ai_reply, tools_used, started, False)
    return ChatResponse(reply=ai_reply)


@router.get("/history", response_model=list[MessageResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.id.desc())
        .all()
    )