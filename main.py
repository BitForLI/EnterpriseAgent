"""本地命令行与 Web 启动入口。"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from src.service import CustomerServiceAgent


async def run_cli() -> None:
    agent = CustomerServiceAgent()
    session_id = uuid.uuid4().hex
    print("企业智能客服已启动（输入 exit 退出）")
    print("可询问商品、订单、退换货政策，或要求人工客服。")

    while True:
        user_input = input("\n用户: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = await agent.chat(user_input, session_id=session_id)
        print(f"\n客服: {result.response}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="企业智能客服 Agent")
    parser.add_argument("--web", action="store_true", help="启动 Web 聊天界面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.web:
        import uvicorn

        uvicorn.run("src.api:api", host=args.host, port=args.port)
    else:
        asyncio.run(run_cli())
