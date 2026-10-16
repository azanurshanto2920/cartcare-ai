import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Message, User
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.agent import generate_reply_with_tools
from app.services.llm import build_user_turn
from app.services.rag import chunk_text, extract_pdf_text, index_chunks, search_context

router = APIRouter(tags=["chat"])

HISTORY_LIMIT = 10


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    filename = (file.filename or "").lower()

    if filename.endswith(".txt"):
        text = file.file.read().decode("utf-8", errors="ignore")
    elif filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        try:
            text = extract_pdf_text(temp_path)
        finally:
            os.remove(temp_path)
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    chunks = chunk_text(text)
    count = index_chunks(chunks)

    return {"message": f"Uploaded and indexed {count} chunks from {file.filename}"}


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Load only this user's recent messages
    recent = (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.timestamp.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    recent.reverse()
    history = [{"role": m.role, "content": m.content} for m in recent]

    # Search the knowledge base; continue without context if it fails
    try:
        doc_context = search_context(request.message)
    except Exception as e:
        print(f"RAG search error: {e}")
        doc_context = ""

    user_turn = build_user_turn(request.message, doc_context)

    try:
        ai_reply = generate_reply_with_tools(db, history, user_turn)
    except Exception as e:
        print(f"LLM error: {e}")
        return ChatResponse(reply="Sorry, there was a problem generating a response. Please try again.")

    # Save both messages only after a successful reply
    db.add(Message(user_id=current_user.id, role="user", content=request.message))
    db.add(Message(user_id=current_user.id, role="assistant", content=ai_reply))
    db.commit()

    return ChatResponse(reply=ai_reply)


@router.get("/history", response_model=list[MessageResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Message)
        .filter(Message.user_id == current_user.id)
        .order_by(Message.timestamp.desc())
        .all()
    )