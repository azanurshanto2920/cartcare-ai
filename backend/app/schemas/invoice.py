from pydantic import BaseModel, Field


class InvoiceItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float | None = None


class InvoiceAdjustment(BaseModel):
    # Discounts are negative, taxes and shipping are positive
    label: str
    amount: float


class ExtractedInvoice(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = Field(default=None, description="ISO format YYYY-MM-DD")
    currency: str = "USD"
    items: list[InvoiceItem] = []
    subtotal: float | None = None
    adjustments: list[InvoiceAdjustment] = []
    total: float | None = None


class InvoiceResult(BaseModel):
    id: int
    filename: str
    needs_review: bool
    warnings: list[str]
    invoice: ExtractedInvoice