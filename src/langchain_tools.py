"""LangChain 工具定义。"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from src.business_tools import create_support_ticket, get_user_orders, search_product_catalog


@tool
def catalog_search(query: str, limit: int = 3) -> dict[str, Any]:
    """按需求搜索商品目录、价格、库存与卖点。"""
    return search_product_catalog(query, limit)


@tool
def order_lookup(user_id: int | None = None, order_id: int | None = None) -> dict[str, Any]:
    """根据用户 ID 或订单号查询订单和物流状态。"""
    return get_user_orders(user_id=user_id, order_id=order_id)


@tool
def human_handoff(
    summary: str, user_id: int | None = None, priority: str = "normal"
) -> dict[str, Any]:
    """创建人工客服工单，返回可追踪的工单号。"""
    return create_support_ticket(summary, user_id=user_id, priority=priority)


TOOL_REGISTRY = {
    "catalog_search": catalog_search,
    "order_lookup": order_lookup,
    "human_handoff": human_handoff,
}
