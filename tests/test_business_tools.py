from pathlib import Path

from src.business_tools import get_user_orders, search_product_catalog
from src.tickets import TicketStore


def test_catalog_search_returns_office_laptop():
    result = search_product_catalog("推荐办公电脑")

    assert result["products"][0]["name"] == "Nimbus Pro 笔记本"


def test_order_lookup_by_user():
    result = get_user_orders(user_id=101)

    assert len(result["orders"]) == 2


def test_order_id_and_user_id_must_match():
    result = get_user_orders(user_id=101, order_id=9003)

    assert result["orders"] == []


def test_ticket_store_persists_ticket(tmp_path: Path):
    store = TicketStore(tmp_path / "tickets.db")
    ticket = store.create("订单投诉", 101, "high")

    assert store.get(str(ticket["id"]))["status"] == "open"
