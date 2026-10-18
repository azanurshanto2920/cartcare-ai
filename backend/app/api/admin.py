import json
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.db.database import get_db
from app.db.models import InvoiceRecord, Ticket, User
from app.schemas.invoice import ExtractedInvoice, InvoiceResult
from app.schemas.ticket import TicketResponse, TicketStatusUpdate
from app.services.invoices import check_invoice, extract_invoice
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


def to_invoice_result(record: InvoiceRecord) -> InvoiceResult:
    return InvoiceResult(
        id=record.id,
        filename=record.filename,
        needs_review=bool(record.needs_review),
        warnings=json.loads(record.warnings or "[]"),
        invoice=ExtractedInvoice.model_validate(json.loads(record.data)),
    )


@router.post("/invoices", response_model=InvoiceResult)
def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf invoices are supported")

    data = file.file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (10 MB maximum)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(data)
        temp_path = tmp.name
    try:
        text = extract_pdf_text(temp_path)
    except Exception:
        raise HTTPException(status_code=400, detail="This PDF could not be opened")
    finally:
        os.remove(temp_path)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found. Scanned invoices without selectable text are not supported.",
        )

    try:
        invoice = extract_invoice(text)
    except Exception as e:
        print(f"Invoice extraction error: {e}")
        raise HTTPException(status_code=502, detail="Could not read this invoice. Please try again.")

    warnings = check_invoice(invoice)

    record = InvoiceRecord(
        uploaded_by=admin.id,
        filename=filename,
        vendor=invoice.vendor,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        total=invoice.total,
        needs_review=bool(warnings),
        warnings=json.dumps(warnings),
        data=invoice.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return to_invoice_result(record)


@router.get("/invoices")
def list_invoices(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    records = db.query(InvoiceRecord).order_by(InvoiceRecord.id.desc()).all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "vendor": r.vendor,
            "invoice_number": r.invoice_number,
            "invoice_date": r.invoice_date,
            "total": r.total,
            "needs_review": bool(r.needs_review),
            "created_at": r.created_at,
        }
        for r in records
    ]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResult)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    record = db.query(InvoiceRecord).filter(InvoiceRecord.id == invoice_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return to_invoice_result(record)