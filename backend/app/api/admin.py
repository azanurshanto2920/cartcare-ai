import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.db.models import Ticket, User
from app.schemas.ticket import TicketResponse, TicketStatusUpdate
from app.services.rag import (
    chunk_text,
    delete_document,
    extract_pdf_text,
    index_document,
    list_documents,
)

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_STATUSES = {"open", "resolved"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("/tickets", response_model=list[TicketResponse])
def list_tickets(
    status: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    return query.order_by(Ticket.created_at.desc()).all()


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: int,
    update: TicketStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    if update.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Status must be 'open' or 'resolved'")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = update.status
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/documents")
def get_documents(admin: User = Depends(get_current_admin)):
    return list_documents()


@router.post("/documents")
def upload_document(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
):
    filename = os.path.basename(file.filename or "")
    if not filename:
        raise HTTPException(status_code=400, detail="The file has no name")

    data = file.file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (10 MB maximum)")

    lowered = filename.lower()
    if lowered.endswith(".txt"):
        text = data.decode("utf-8", errors="ignore")
    elif lowered.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(data)
            temp_path = tmp.name
        try:
            text = extract_pdf_text(temp_path)
        finally:
            os.remove(temp_path)
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the file")

    count = index_document(filename, chunk_text(text))
    return {"source": filename, "chunks": count}


@router.delete("/documents/{source}")
def remove_document(source: str, admin: User = Depends(get_current_admin)):
    removed = delete_document(source)
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"source": source, "chunks_removed": removed}