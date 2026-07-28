#自定义业务工具的MCP服务端

import httpx
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务端
mcp = FastMCP("DummyJSON-Ecommerce-Tools")


# 1. 售前工具：搜索商品与库存
@mcp.tool()
async def search_product_catalog(query: str) -> str:
    """
    根据关键词搜索商品列表、价格、库存及详细描述。
    适用于售前咨询、推荐商品或核对库存。
    """
    url = f"https://dummyjson.com/products/search?q={query}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])

                if not products:
                    return f"【系统提示】未找到与 '{query}' 相关的商品。"

                # 清洗数据：只抽取核心字段节省 Token
                results = []
                for p in products[:3]:  # 取匹配度最高的 3 个商品
                    results.append(
                        f"- 商品ID: {p['id']} | 名称: {p['title']} | 价格: ${p['price']} "
                        f"| 库存: {p['stock']}件 | 品牌: {p['brand']}\n  简介: {p['description']}"
                    )
                return "\n".join(results)
            return f"【接口报错】网络请求异常，状态码: {response.status_code}"
        except Exception as e:
            return f"【系统异常】调用商品接口失败，原因: {str(e)}"


# 2. 售后工具：查询用户订单/购物车状态
@mcp.tool()
async def get_user_orders(user_id: int) -> str:
    """
    根据数字类型的用户 ID (user_id)，查询该用户最近的订单及购物车商品详情。
    适用于售后查询、物流进度或修改订单。
    """
    url = f"https://dummyjson.com/carts/user/{user_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                carts = data.get("carts", [])

                if not carts:
                    return f"【系统提示】用户 ID {user_id} 当前没有任何订单或购物车记录。"

                # 拼接订单文本
                orders_summary = []
                for cart in carts:
                    items = [f"{item['title']} (单价:${item['price']} x{item['quantity']})" for item in
                             cart['products']]
                    orders_summary.append(
                        f"📦 订单号 #{cart['id']} | 原价: ${cart['total']} | 折后价: ${cart['discountedTotal']}\n"
                        f"   包含商品: {', '.join(items)}"
                    )
                return "\n".join(orders_summary)
            elif response.status_code == 404:
                return f"【参数错误】不存在用户 ID 为 {user_id} 的账户，请提示用户核对 ID。"
            return f"【接口报错】HTTP 状态码: {response.status_code}"
        except Exception as e:
            return f"【系统异常】网络超时或请求失败: {str(e)}"


if __name__ == "__main__":
    # 启动 MCP 服务端
    mcp.run()