"""可被 LangChain Agent 与 MCP 共同复用的业务能力。"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from src.config import settings
from src.tickets import TicketStore


@lru_cache(maxsize=4)
def _load_json(filename: str) -> list[dict[str, Any]]:
    return json.loads((settings.data_dir / filename).read_text(encoding="utf-8"))


def _keywords(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", text.lower()))


def search_product_catalog(query: str, limit: int = 3) -> dict[str, Any]:
    products = _load_json("catalog.json")
    query_lower = query.lower()
    query_words = _keywords(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for product in products:
        searchable = " ".join(
            [product["name"], product["category"], product["description"], *product["tags"]]
        ).lower()
        score = sum(word in searchable for word in query_words)
        score += sum(tag.lower() in query_lower for tag in product["tags"]) * 2
        if score or product["category"].lower() in query_lower:
            ranked.append((score, product))

    if not ranked:
        ranked = [(0, product) for product in products if product["stock"] > 0]
    ranked.sort(key=lambda item: (item[0], item[1]["rating"]), reverse=True)
    return {"products": [product for _, product in ranked[: max(1, min(limit, 5))]]}


def get_user_orders(
    user_id: int | None = None, order_id: int | None = None
) -> dict[str, Any]:
    orders = _load_json("orders.json")
    if order_id is not None:
        matches = [order for order in orders if order["id"] == order_id]
        if user_id is not None:
            matches = [order for order in matches if order["user_id"] == user_id]
    elif user_id is not None:
        matches = [order for order in orders if order["user_id"] == user_id]
    else:
        matches = []
    return {"orders": matches, "user_id": user_id, "order_id": order_id}


def create_support_ticket(
    summary: str, user_id: int | None = None, priority: str = "normal"
) -> dict[str, Any]:
    allowed_priority = priority if priority in {"low", "normal", "high"} else "normal"
    return TicketStore().create(summary.strip()[:500], user_id, allowed_priority)
