"""将 Agent 使用的同一套业务能力暴露为 MCP 工具。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from src.business_tools import (
    create_support_ticket,
    get_user_orders,
    search_product_catalog,
)


mcp = FastMCP("Enterprise-Customer-Service")


@mcp.tool()
def search_products(query: str, limit: int = 3) -> dict[str, Any]:
    """搜索商品、价格和库存。"""
    return search_product_catalog(query, limit)


@mcp.tool()
def lookup_orders(
    user_id: int | None = None, order_id: int | None = None
) -> dict[str, Any]:
    """通过用户 ID 或订单号查询订单。"""
    return get_user_orders(user_id=user_id, order_id=order_id)


@mcp.tool()
def escalate_to_human(
    summary: str, user_id: int | None = None, priority: str = "normal"
) -> dict[str, Any]:
    """创建人工客服工单。"""
    return create_support_ticket(summary, user_id=user_id, priority=priority)


if __name__ == "__main__":
    mcp.run()
