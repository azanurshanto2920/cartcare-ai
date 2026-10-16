from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Product


def search_products(
    db: Session,
    query: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    limit: int = 5,
) -> list[dict]:
    q = db.query(Product)

    if query:
        # Every word must match the name, brand, category or description
        for word in query.split():
            pattern = f"%{word}%"
            q = q.filter(
                or_(
                    Product.name.ilike(pattern),
                    Product.brand.ilike(pattern),
                    Product.category.ilike(pattern),
                    Product.description.ilike(pattern),
                )
            )

    if category:
        q = q.filter(Product.category.ilike(category))
    if brand:
        q = q.filter(Product.brand.ilike(brand))
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if in_stock_only:
        q = q.filter(Product.stock > 0)

    products = q.order_by(Product.price.asc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "brand": p.brand,
            "price": p.price,
            "in_stock": p.stock > 0,
            "description": p.description,
        }
        for p in products
    ]