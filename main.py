import asyncio
from src.agent_graph import app


async def main():
    print("智能客服 Agent 系统已启动（输入 'exit' 退出）")
    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # 运行图并传入初始状态
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        result = await app.ainvoke(initial_state)

        # 打印 Agent 最终回复
        last_msg = result["messages"][-1]
        print(f"\nAgent: {last_msg['content']}")


if __name__ == "__main__":
    asyncio.run(main())
