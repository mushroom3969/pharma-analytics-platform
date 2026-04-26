from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = PROJECT_ROOT / "data" / "products.json"

DEFAULT_CATEGORIES = ["scale", "production_area", "process_steps"]


@dataclass
class Product:
    product_id: str
    name: str
    created_at: str
    sub_items: dict = field(default_factory=dict)  # {category: [values]}

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "created_at": self.created_at,
            "sub_items": self.sub_items,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Product:
        return cls(
            product_id=d["product_id"],
            name=d["name"],
            created_at=d["created_at"],
            sub_items=d.get("sub_items", {}),
        )


def list_products() -> list[Product]:
    if not PRODUCTS_PATH.exists():
        return []
    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        return [Product.from_dict(r) for r in json.load(f)]


def get_product(product_id: str) -> Product | None:
    return next((p for p in list_products() if p.product_id == product_id), None)


def create_product(name: str) -> Product:
    product = Product(
        product_id=str(uuid.uuid4()),
        name=name,
        created_at=datetime.now().isoformat(timespec="seconds"),
        sub_items={cat: [] for cat in DEFAULT_CATEGORIES},
    )
    save_product(product)
    return product


def save_product(product: Product) -> None:
    products = list_products()
    updated = [product if p.product_id == product.product_id else p for p in products]
    if not any(p.product_id == product.product_id for p in products):
        updated.append(product)
    _write(updated)


def delete_product(product_id: str) -> bool:
    products = list_products()
    remaining = [p for p in products if p.product_id != product_id]
    if len(remaining) == len(products):
        return False
    _write(remaining)
    return True


def _write(products: list[Product]) -> None:
    PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        json.dump([p.to_dict() for p in products], f, ensure_ascii=False, indent=2)
