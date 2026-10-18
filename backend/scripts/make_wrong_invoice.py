from scripts.make_sample_invoices import INVOICES, OUT_DIR, calculate, draw_pdf

# Same as the Northwind invoice, but the printed total is $100 too high
invoice = dict(INVOICES[0])
invoice["file"] = "invoice_wrong_total.pdf"
invoice["number"] = "INV-2026-0999"

subtotal, lines, total = calculate(invoice)
OUT_DIR.mkdir(parents=True, exist_ok=True)
draw_pdf(OUT_DIR / invoice["file"], invoice, subtotal, lines, total + 100)

print(f"Saved {invoice['file']}: real total {total}, printed total {round(total + 100, 2)}")