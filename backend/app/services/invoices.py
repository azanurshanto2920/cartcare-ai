import json
import re

from pydantic import ValidationError

from app.core.config import settings
from app.schemas.invoice import ExtractedInvoice
from app.services.llm import client

MAX_TEXT_CHARS = 15000
TOLERANCE = 0.01

SYSTEM_PROMPT = (
    "You extract data from invoice text and reply with a single JSON object and nothing else. "
    "Use exactly these keys: "
    "vendor (string), invoice_number (string), invoice_date (string, format YYYY-MM-DD), "
    "currency (string, for example USD), "
    "items (list of objects with description, quantity, unit_price, line_total), "
    "subtotal (number), "
    "adjustments (list of objects with label and amount), "
    "total (number). "
    "Rules: "
    "Numbers must be plain numbers without currency symbols or thousands separators. "
    "Put discounts, taxes, shipping and similar extra lines in adjustments. "
    "A discount must have a negative amount. Taxes and shipping must be positive. "
    "Do not put the subtotal or the total in adjustments. "
    "Only list real product or service lines in items. "
    "Copy the subtotal and the total exactly as printed. Never calculate or guess them. "
    "Read dates carefully: if the date is written like 12/10/2026 and the document says DD/MM/YYYY, "
    "it is 12 October 2026. "
    "If a value is not in the text, use null. Never invent values."
)


def extract_invoice(text: str) -> ExtractedInvoice:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Invoice text:\n\n{text[:MAX_TEXT_CHARS]}"},
    ]

    last_error: Exception | None = None
    for _ in range(2):  # one retry if the reply is not valid
        completion = client.chat.completions.create(
            messages=messages,
            model=settings.llm_model,
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=2000,
        )
        raw = completion.choices[0].message.content or ""
        try:
            return ExtractedInvoice.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e

    raise ValueError(f"Could not read the invoice: {last_error}")


def check_invoice(invoice: ExtractedInvoice) -> list[str]:
    warnings: list[str] = []

    if not invoice.vendor:
        warnings.append("Vendor name is missing.")
    if not invoice.invoice_number:
        warnings.append("Invoice number is missing.")
    if not invoice.invoice_date:
        warnings.append("Invoice date is missing.")
    elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", invoice.invoice_date):
        warnings.append(f"Invoice date '{invoice.invoice_date}' is not in YYYY-MM-DD format.")
    if invoice.total is None:
        warnings.append("Total is missing.")
    if not invoice.items:
        warnings.append("No line items were found.")

    items_sum = 0.0
    for item in invoice.items:
        expected = round(item.quantity * item.unit_price, 2)
        if item.line_total is not None and abs(item.line_total - expected) > TOLERANCE:
            warnings.append(
                f"Line '{item.description}': {item.quantity} x {item.unit_price} is {expected}, "
                f"but the invoice shows {item.line_total}."
            )
        items_sum += item.line_total if item.line_total is not None else expected
    items_sum = round(items_sum, 2)

    if invoice.subtotal is not None and invoice.items:
        if abs(invoice.subtotal - items_sum) > TOLERANCE:
            warnings.append(
                f"The line items add up to {items_sum}, but the subtotal is {invoice.subtotal}."
            )

    base = invoice.subtotal if invoice.subtotal is not None else items_sum
    adjustments_sum = round(sum(a.amount for a in invoice.adjustments), 2)
    if invoice.total is not None and abs(base + adjustments_sum - invoice.total) > TOLERANCE:
        warnings.append(
            f"Subtotal {base} plus adjustments {adjustments_sum} is {round(base + adjustments_sum, 2)}, "
            f"but the total is {invoice.total}."
        )

    return warnings