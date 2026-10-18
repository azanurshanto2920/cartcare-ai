import json
from pathlib import Path

from app.services.invoices import check_invoice, extract_invoice
from app.services.rag import extract_pdf_text

FOLDER = Path(__file__).resolve().parents[2] / "docs" / "sample_invoices"
TOLERANCE = 0.01


def same_number(got, want) -> bool:
    return got is not None and abs(got - want) <= TOLERANCE


def main() -> None:
    expected_list = json.loads((FOLDER / "expected.json").read_text(encoding="utf-8"))
    passed = 0

    for expected in expected_list:
        name = expected["file"]
        print(f"\n{name}")

        try:
            text = extract_pdf_text(str(FOLDER / name))
            result = extract_invoice(text)
        except Exception as e:
            print(f"  FAILED to extract: {e}")
            continue

        problems = []
        if result.vendor != expected["vendor"]:
            problems.append(f"vendor is {result.vendor!r}, expected {expected['vendor']!r}")
        if result.invoice_number != expected["invoice_number"]:
            problems.append(f"invoice number is {result.invoice_number!r}, expected {expected['invoice_number']!r}")
        if result.invoice_date != expected["invoice_date"]:
            problems.append(f"date is {result.invoice_date!r}, expected {expected['invoice_date']!r}")
        if not same_number(result.subtotal, expected["subtotal"]):
            problems.append(f"subtotal is {result.subtotal}, expected {expected['subtotal']}")
        if not same_number(result.total, expected["total"]):
            problems.append(f"total is {result.total}, expected {expected['total']}")

        if len(result.items) != len(expected["items"]):
            problems.append(f"found {len(result.items)} items, expected {len(expected['items'])}")
        else:
            for got, want in zip(result.items, expected["items"]):
                if (
                    got.description.strip().lower() != want["description"].lower()
                    or not same_number(got.quantity, want["quantity"])
                    or not same_number(got.unit_price, want["unit_price"])
                ):
                    problems.append(f"item differs: {got.description!r} x{got.quantity} at {got.unit_price}")

        warnings = check_invoice(result)

        if problems:
            print("  MISMATCH")
            for problem in problems:
                print(f"    - {problem}")
        else:
            print("  OK, matches the expected data")
            passed += 1

        if warnings:
            print("  Checker warnings:")
            for warning in warnings:
                print(f"    - {warning}")
        else:
            print("  Checker: no warnings")

    print(f"\nPassed {passed} of {len(expected_list)}")


if __name__ == "__main__":
    main()