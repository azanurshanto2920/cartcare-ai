import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT_DIR = Path(__file__).resolve().parents[2] / "docs" / "sample_invoices"

INVOICES = [
    {
        "file": "invoice_northwind.pdf",
        "vendor": "Northwind Appliances Ltd",
        "vendor_address": "14 Harbor Road, Springfield",
        "title": "INVOICE",
        "number_label": "Invoice No",
        "number": "INV-2026-0412",
        "date_label": "Invoice Date",
        "date_text": "September 14, 2026",
        "iso_date": "2026-09-14",
        "customer_label": "Bill To",
        "customer": "CartCare Store",
        "columns": ["Description", "Qty", "Unit Price", "Amount"],
        "items": [
            ("Samsung 43 inch Full HD Smart TV", 2, 429.00),
            ("LG 190L Single Door Refrigerator", 1, 329.00),
        ],
        "adjustments": [("Sales Tax (8%)", "percent_tax", 8)],
        "total_label": "Total Due",
    },
    {
        "file": "invoice_brighthome.pdf",
        "vendor": "BrightHome Supply Co.",
        "vendor_address": "220 Market Street, Lakeview",
        "title": "TAX INVOICE",
        "number_label": "Invoice #",
        "number": "BH-88213",
        "date_label": "Date",
        "date_text": "03 Oct 2026",
        "iso_date": "2026-10-03",
        "customer_label": "Customer",
        "customer": "CartCare Store",
        "columns": ["Item", "Qty", "Price", "Line Total"],
        "items": [
            ("Carrier 1.5 Ton Inverter AC", 3, 749.00),
            ("AC installation service", 3, 45.00),
        ],
        "adjustments": [
            ("Volume discount (5%)", "percent_discount", 5),
            ("Shipping", "flat", 25.00),
        ],
        "total_label": "Grand Total",
    },
    {
        "file": "invoice_metro_wholesale.pdf",
        "vendor": "Metro Wholesale Traders",
        "vendor_address": "9 Industrial Estate, Riverside",
        "title": "BILL",
        "number_label": "Bill No",
        "number": "7731",
        "date_label": "Billed on (DD/MM/YYYY)",
        "date_text": "12/10/2026",
        "iso_date": "2026-10-12",
        "customer_label": "Supplier of",
        "customer": "CartCare Store",
        "columns": ["Description", "Qty", "Rate", "Amt"],
        "items": [
            ("Midea 2 Ton Inverter AC", 2, 949.00),
            ("Hisense 500L Side by Side Refrigerator", 1, 1399.00),
        ],
        "adjustments": [("VAT (5%)", "percent_tax", 5)],
        "total_label": "Amount Due",
    },
]


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def calculate(invoice: dict):
    items = invoice["items"]
    subtotal = round(sum(qty * price for _, qty, price in items), 2)
    total = subtotal
    lines = []
    for label, kind, value in invoice["adjustments"]:
        if kind == "percent_discount":
            amount = -round(subtotal * value / 100, 2)
        elif kind == "percent_tax":
            amount = round(subtotal * value / 100, 2)
        else:
            amount = value
        total = round(total + amount, 2)
        lines.append((label, amount))
    return subtotal, lines, total


def draw_pdf(path: Path, invoice: dict, subtotal: float, lines: list, total: float) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - 60

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, invoice["vendor"])
    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, invoice["vendor_address"])

    y -= 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, invoice["title"])

    pdf.setFont("Helvetica", 11)
    y -= 24
    pdf.drawString(50, y, f'{invoice["number_label"]}: {invoice["number"]}')
    y -= 16
    pdf.drawString(50, y, f'{invoice["date_label"]}: {invoice["date_text"]}')
    y -= 16
    pdf.drawString(50, y, f'{invoice["customer_label"]}: {invoice["customer"]}')

    columns_x = [50, 330, 390, 480]
    y -= 36
    pdf.setFont("Helvetica-Bold", 10)
    for x, header in zip(columns_x, invoice["columns"]):
        pdf.drawString(x, y, header)
    y -= 6
    pdf.line(50, y, 545, y)

    pdf.setFont("Helvetica", 10)
    y -= 16
    for description, qty, price in invoice["items"]:
        pdf.drawString(columns_x[0], y, description)
        pdf.drawString(columns_x[1], y, str(qty))
        pdf.drawString(columns_x[2], y, money(price))
        pdf.drawString(columns_x[3], y, money(qty * price))
        y -= 16

    y -= 4
    pdf.line(50, y, 545, y)
    y -= 20

    rows = [("Subtotal", subtotal)] + lines
    for label, amount in rows:
        pdf.drawString(330, y, label)
        pdf.drawRightString(545, y, money(amount))
        y -= 16

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(330, y - 4, invoice["total_label"])
    pdf.drawRightString(545, y - 4, money(total))

    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, 60, "Payment due within 30 days. Thank you for your business.")
    pdf.save()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    expected = []

    for invoice in INVOICES:
        subtotal, lines, total = calculate(invoice)
        draw_pdf(OUT_DIR / invoice["file"], invoice, subtotal, lines, total)
        expected.append(
            {
                "file": invoice["file"],
                "invoice_number": invoice["number"],
                "invoice_date": invoice["iso_date"],
                "vendor": invoice["vendor"],
                "subtotal": subtotal,
                "total": total,
                "items": [
                    {"description": d, "quantity": q, "unit_price": p}
                    for d, q, p in invoice["items"]
                ],
            }
        )
        print(f'{invoice["file"]}: subtotal {subtotal}, total {total}')

    (OUT_DIR / "expected.json").write_text(json.dumps(expected, indent=2), encoding="utf-8")
    print(f"Saved {len(expected)} invoices and expected.json to {OUT_DIR}")


if __name__ == "__main__":
    main()

    